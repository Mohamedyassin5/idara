"""
Run Routing Evals
=================

python -m evals                # run all routing cases against the Master Orchestrator
python -m evals --case <name>  # run one case

Each case sends one question to `master_orchestrator` and reads which agent actually answered from the
nested `member_responses` of the returned TeamRunOutput (orchestrator run -> hub TeamRunOutput -> agent
RunOutput, whose `agent_id` is the final agent). A case passes when exactly one final agent answered and
it is the expected one.

Pacing: cases are spaced by PACING_SECONDS (each agent call embeds the query with Voyage, whose free
tier allows 3 requests/minute), the same 21s used for indexing in app/main.py.

Exit 0 when every case passes, 1 on any failure or error, 2 on an unknown --case.
"""

# Hydrate os.environ from .env before any module that reads env at import time
# (API keys are read when the agents are imported). Pre-existing shell vars take precedence.
from evals.dotenv import load_dotenv

load_dotenv()

import time  # noqa: E402
from dataclasses import dataclass, field  # noqa: E402
from uuid import uuid4  # noqa: E402

import typer  # noqa: E402
from agno.run.agent import RunOutput  # noqa: E402
from agno.run.team import TeamRunOutput  # noqa: E402
from rich.console import Console  # noqa: E402
from rich.table import Table  # noqa: E402

from agents.admin_utilities.bureaucratie_agent import load_bureaucratie_knowledge  # noqa: E402
from agents.admin_utilities.entrepreneuriat_agent import load_entrepreneuriat_knowledge  # noqa: E402
from agents.admin_utilities.steg_agent import load_steg_knowledge  # noqa: E402
from agents.education_work.bac_agent import load_bac_knowledge  # noqa: E402
from agents.education_work.job_agent import load_job_knowledge  # noqa: E402
from agents.housing_community.immobilier_agent import load_immobilier_knowledge  # noqa: E402
from agents.mobility_city.louage_agent import load_louage_knowledge  # noqa: E402
from agents.mobility_city.parking_agent import load_parking_knowledge  # noqa: E402
from agents.mobility_city.souk_agent import load_souk_knowledge  # noqa: E402
from agents.orchestrator import master_orchestrator  # noqa: E402
from evals.cases import CASES, RoutingCase  # noqa: E402

PACING_SECONDS = 21  # Voyage free tier: 3 requests/minute
RETRY_WAIT_SECONDS = 45  # single retry after a failed run (rate limit / transient provider error)

app = typer.Typer(add_completion=False, no_args_is_help=False, pretty_exceptions_show_locals=False)
console = Console()


@dataclass
class CaseOutcome:
    case: RoutingCase
    got_agents: list[str] = field(default_factory=list)  # final agent id(s) that produced an answer
    got_paths: list[str] = field(default_factory=list)  # e.g. "master-orchestrator > steg-hub > steg-agent"
    seconds: float = 0.0
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.error is None and self.got_agents == [self.case.expected_agent]

    @property
    def got_label(self) -> str:
        if self.error:
            return f"(erreur) {self.error}"
        return ", ".join(self.got_agents) if self.got_agents else "(aucun agent : l'orchestrateur a répondu seul)"


def final_agent_paths(run: TeamRunOutput | RunOutput, prefix: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
    """Return every delegation path ending on an agent run, e.g. (team, hub, agent).

    A TeamRunOutput lists the runs of the members it delegated to in `member_responses`; a member that is
    itself a Team appears as a nested TeamRunOutput, a plain Agent as a RunOutput (the leaf, with `agent_id`).
    """
    if isinstance(run, RunOutput):
        return [(*prefix, run.agent_id or "?")]
    paths: list[tuple[str, ...]] = []
    here = (*prefix, run.team_id or "?")
    for member in run.member_responses:
        paths.extend(final_agent_paths(member, here))
    return paths


def ensure_knowledge() -> None:
    """Same indexing step as the AgentOS lifespan in app/main.py: no Voyage call when already indexed."""
    embedded = 0
    for load in (
        load_bureaucratie_knowledge,
        load_steg_knowledge,
        load_louage_knowledge,
        load_parking_knowledge,
        load_souk_knowledge,
        load_bac_knowledge,
        load_job_knowledge,
        load_immobilier_knowledge,
        load_entrepreneuriat_knowledge,
    ):
        if embedded:
            time.sleep(PACING_SECONDS)
        embedded = load(PACING_SECONDS)


def run_case(case: RoutingCase) -> CaseOutcome:
    outcome = CaseOutcome(case=case)
    start = time.monotonic()
    for attempt in (1, 2):
        try:
            # Fresh session per case: the orchestrator keeps history (add_history_to_context), and earlier
            # questions must not steer the routing of later ones.
            run = master_orchestrator.run(
                input=case.question,
                session_id=f"eval-{case.name}-{uuid4().hex[:8]}",
                user_id="routing-eval",
            )
            paths = final_agent_paths(run)
            outcome.got_paths = [" > ".join(p) for p in paths]
            outcome.got_agents = [p[-1] for p in paths]
            outcome.error = None
            break
        except Exception as exc:
            outcome.error = f"{type(exc).__name__}: {exc}"
            if attempt == 1:
                console.print(f"  [yellow]run failed ({outcome.error}); retry in {RETRY_WAIT_SECONDS}s[/yellow]")
                time.sleep(RETRY_WAIT_SECONDS)
    outcome.seconds = time.monotonic() - start
    return outcome


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    case: str = typer.Option(None, "--case", help="Run only this case by name"),
) -> None:
    """Run the routing eval suite, or one case with --case <name>."""
    if ctx.invoked_subcommand is not None:
        return

    cases = list(CASES)
    if case:
        cases = [c for c in cases if c.name == case]
        if not cases:
            console.print(f"[red]no case named[/red] {case!r}")
            console.print(f"  [dim]available:[/dim] {', '.join(c.name for c in CASES)}")
            raise typer.Exit(2)

    console.print("[dim]checking knowledge bases…[/dim]")
    ensure_knowledge()

    outcomes: list[CaseOutcome] = []
    for i, c in enumerate(cases, 1):
        if i > 1:
            time.sleep(PACING_SECONDS)
        console.rule(f"[bold]{c.name}[/bold]  [dim]{c.kind} · {i}/{len(cases)}[/dim]")
        console.print(f"[dim]Q:[/dim] {c.question}")
        o = run_case(c)
        outcomes.append(o)
        style = "green" if o.passed else "red"
        console.print(
            f"[{style}]{'PASS' if o.passed else 'FAIL'}[/{style}]  "
            f"expected [bold]{c.expected_agent}[/bold], got [bold]{o.got_label}[/bold]  [dim]({o.seconds:.1f}s)[/dim]"
        )
        for path in o.got_paths:
            console.print(f"  [dim]path: {path}[/dim]")

    table = Table(title="Routing Eval Summary", title_style="bold sky_blue1", show_header=True, header_style="bold")
    table.add_column("Case", overflow="fold")
    table.add_column("Kind")
    table.add_column("Expected")
    table.add_column("Got", overflow="fold")
    table.add_column("Status")
    for o in outcomes:
        status = "[green]PASS[/green]" if o.passed else "[red]FAIL[/red]"
        table.add_row(o.case.name, o.case.kind, o.case.expected_agent, o.got_label, status)
    console.print()
    console.print(table)

    total = len(outcomes)
    passed = sum(1 for o in outcomes if o.passed)
    failed = total - passed
    console.print(f"\n[bold]Cases:[/bold] {total}   [green]passed: {passed}[/green]   [red]failed: {failed}[/red]")
    console.print(f"[bold]Success rate:[/bold] {100 * passed / total:.1f}%")

    if failed:
        console.print("\n[bold red]Failures[/bold red]")
        for o in outcomes:
            if not o.passed:
                console.print(f"  [bold]{o.case.name}[/bold] ({o.case.kind})")
                console.print(f"    question: {o.case.question}")
                console.print(f"    expected: {o.case.expected_agent} (hub: {o.case.expected_hub})")
                console.print(f"    got:      {o.got_label}")
                for path in o.got_paths:
                    console.print(f"    path:     {path}")

    raise typer.Exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    app()
