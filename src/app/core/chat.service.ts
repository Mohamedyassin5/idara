import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { catchError, map, Observable, throwError, timeout } from 'rxjs';

/** A named, located result set an agent attaches to its answer (e.g. parkings, louage stations). */
export interface GeoPayload {
  type: string;
  items: Record<string, unknown>[];
}

export interface Answer {
  content: string;
  /** Backend id of the agent that actually produced the answer (e.g. "steg-agent"), if the run exposed it. */
  agentId: string | null;
  /** Delegation path, e.g. ["master-orchestrator", "admin-utilities-hub", "steg-agent"]. */
  path: string[];
  /** Structured map result extracted from a ```geo fenced block, if the answer carried one. */
  geo: GeoPayload | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'error';
  text: string;
  agentId?: string | null;
  geo?: GeoPayload | null;
}

const GEO_BLOCK = /```geo\s*([\s\S]*?)```/;

/** A saved conversation (one AgentOS session). Pin and archive live in its metadata. */
export interface SessionSummary {
  session_id: string;
  session_name: string;
  updated_at: string;
  metadata: { domain?: string; pinned?: boolean; archived?: boolean } | null;
}

const SESSIONS_URL = '/api/sessions';
const DOMAIN_PREFIX = /^\[Domaine : [^\]]*\]\s*/;

/** Pulls the agent's ```geo payload out of its markdown answer, so it renders as a map, not raw JSON text. */
export function parseAnswer(content: string): { text: string; geo: GeoPayload | null } {
  const match = content.match(GEO_BLOCK);
  if (!match) return { text: content, geo: null };
  try {
    const parsed = JSON.parse(match[1].trim()) as GeoPayload;
    if (!parsed?.type || !Array.isArray(parsed.items)) return { text: content, geo: null };
    return { text: content.slice(0, match.index).trim(), geo: parsed };
  } catch {
    return { text: content, geo: null };
  }
}

export class ChatError extends Error {
  constructor(readonly kind: 'backend' | 'generic') {
    super(kind);
  }
}

const RUNS_URL = '/api/teams/master-orchestrator/runs';
const REQUEST_TIMEOUT_MS = 150_000;

// Loose shape of the run JSON returned by AgentOS (TeamRunOutput.to_dict()).
interface RunNode {
  content?: unknown;
  agent_id?: string;
  team_id?: string;
  member_responses?: RunNode[];
}

/** Walk the nested member_responses down to the agent runs: orchestrator -> hub -> agent. */
function agentPaths(node: RunNode, prefix: string[] = []): string[][] {
  if (node.agent_id) return [[...prefix, node.agent_id]];
  const here = [...prefix, node.team_id ?? '?'];
  return (node.member_responses ?? []).flatMap((child) => agentPaths(child, here));
}

@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly http = inject(HttpClient);
  private readonly userId = this.loadUserId();

  /** Conversations kept per page so navigating back keeps the history. */
  private readonly conversations = new Map<string, { messages: ReturnType<typeof signal<ChatMessage[]>>; session: string }>();

  conversation(key: string) {
    let c = this.conversations.get(key);
    if (!c) {
      c = { messages: signal<ChatMessage[]>([]), session: this.newSession() };
      this.conversations.set(key, c);
    }
    return c;
  }

  reset(key: string): void {
    const c = this.conversation(key);
    c.messages.set([]);
    c.session = this.newSession();
  }

  /** Saved conversations of one domain, newest first. */
  listSessions(domain: string): Observable<SessionSummary[]> {
    return this.http.get<{ data: SessionSummary[] }>(SESSIONS_URL, { params: this.sessionParams().set('limit', '100') }).pipe(
      map((res) => res.data.filter((s) => s.metadata?.domain === domain)),
    );
  }

  /** Names a brand-new conversation after its first question so it can be found in the list. */
  tagSession(sessionId: string, domain: string, title: string): Observable<unknown> {
    return this.http.patch(`${SESSIONS_URL}/${encodeURIComponent(sessionId)}`, {
      session_name: title.slice(0, 80),
      metadata: { domain, pinned: false, archived: false },
    }, { params: this.sessionParams() });
  }

  /** Writes the full metadata (pinned/archived) of a saved conversation. */
  updateFlags(sessionId: string, domain: string, flags: { pinned: boolean; archived: boolean }): Observable<unknown> {
    return this.http.patch(`${SESSIONS_URL}/${encodeURIComponent(sessionId)}`, { metadata: { domain, ...flags } }, {
      params: this.sessionParams(),
    });
  }

  deleteSession(sessionId: string): Observable<unknown> {
    return this.http.delete(`${SESSIONS_URL}/${encodeURIComponent(sessionId)}`, { params: this.sessionParams() });
  }

  /** Rebuilds a saved conversation's messages from its top-level runs (question + answer). */
  loadSession(sessionId: string): Observable<ChatMessage[]> {
    return this.http
      .get<{ parent_run_id?: string | null; run_input?: string | null; content?: string | null }[]>(
        `${SESSIONS_URL}/${encodeURIComponent(sessionId)}/runs`,
        { params: this.sessionParams() },
      )
      .pipe(
        map((runs) =>
          runs
            .filter((r) => !r.parent_run_id && r.run_input)
            .flatMap((r): ChatMessage[] => {
              const question = (r.run_input ?? '').replace(DOMAIN_PREFIX, '');
              const { text, geo } = parseAnswer(r.content ?? '');
              return [
                { role: 'user', text: question },
                { role: 'assistant', text, geo, agentId: null },
              ];
            }),
        ),
      );
  }

  private sessionParams(): HttpParams {
    return new HttpParams().set('type', 'team').set('component_id', 'master-orchestrator').set('user_id', this.userId);
  }

  ask(message: string, sessionId: string): Observable<Answer> {
    const body = new FormData();
    body.set('message', message);
    body.set('stream', 'false');
    body.set('session_id', sessionId);
    body.set('user_id', this.userId);

    return this.http.post<RunNode>(RUNS_URL, body).pipe(
      timeout(REQUEST_TIMEOUT_MS),
      map((run) => {
        const paths = agentPaths(run);
        const raw = typeof run.content === 'string' ? run.content : JSON.stringify(run.content ?? '');
        const { text, geo } = parseAnswer(raw);
        // Only report an agent when exactly one answered; several would make the badge misleading.
        const single = paths.length === 1 ? paths[0] : null;
        return { content: text, agentId: single ? single[single.length - 1] : null, path: single ?? [], geo };
      }),
      catchError((err) =>
        throwError(() => new ChatError(err?.status === 0 || err?.status === 502 || err?.status === 504 ? 'backend' : 'generic')),
      ),
    );
  }

  private newSession(): string {
    return `web-${crypto.randomUUID()}`;
  }

  private loadUserId(): string {
    try {
      const saved = localStorage.getItem('idara.userId');
      if (saved) return saved;
      const fresh = `web-user-${crypto.randomUUID()}`;
      localStorage.setItem('idara.userId', fresh);
      return fresh;
    } catch {
      return `web-user-${crypto.randomUUID()}`;
    }
  }
}
