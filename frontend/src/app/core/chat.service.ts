import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { catchError, map, Observable, throwError, timeout } from 'rxjs';

export interface Answer {
  content: string;
  /** Backend id of the agent that actually produced the answer (e.g. "steg-agent"), if the run exposed it. */
  agentId: string | null;
  /** Delegation path, e.g. ["master-orchestrator", "admin-utilities-hub", "steg-agent"]. */
  path: string[];
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'error';
  text: string;
  agentId?: string | null;
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
        const content = typeof run.content === 'string' ? run.content : JSON.stringify(run.content ?? '');
        // Only report an agent when exactly one answered; several would make the badge misleading.
        const single = paths.length === 1 ? paths[0] : null;
        return { content, agentId: single ? single[single.length - 1] : null, path: single ?? [] };
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
