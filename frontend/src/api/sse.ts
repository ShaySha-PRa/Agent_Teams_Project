export interface SSEParseProgress {
  agent_name: string;
  progress_pct: number;
  current_clause_type?: string;
  current_dimension?: string;
}

export interface SSEParseComplete {
  document_id: string;
  clause_count: number;
}

export interface SSEParseFailed {
  error_type: string;
  error_message: string;
  recoverable: boolean;
}

export interface SSEReviewProgress {
  agent_name: string;
  clauses_processed: number;
  total_clauses: number;
  current_dimension?: string;
}

export interface SSEReviewLog {
  timestamp: string;
  agent_name: string;
  message: string;
}

export interface SSEReviewComplete {
  summary: { high: number; medium: number; low: number };
}

export interface SSEReviewFailed {
  fail_category: string;
  message: string;
  partial_results_available: boolean;
}

export interface SSEReviewTimeout {
  completed_count: number;
  total_count: number;
}

export interface SSEInterruptReady {
  interrupt_id: string;
  interrupt_type: string;
  payload: unknown;
}

export interface SSEEventHandler {
  onParseProgress?: (data: SSEParseProgress) => void;
  onParseComplete?: (data: SSEParseComplete) => void;
  onParseFailed?: (data: SSEParseFailed) => void;
  onReviewProgress?: (data: SSEReviewProgress) => void;
  onReviewLog?: (data: SSEReviewLog) => void;
  onReviewComplete?: (data: SSEReviewComplete) => void;
  onReviewFailed?: (data: SSEReviewFailed) => void;
  onReviewTimeout?: (data: SSEReviewTimeout) => void;
  onInterruptReady?: (data: SSEInterruptReady) => void;
}

const BASE_URL = '/api/v1';

export function connectSSE(documentId: string, handlers: SSEEventHandler): { close: () => void } {
  const url = `${BASE_URL}/documents/${documentId}/events`;
  let eventSource: EventSource | null = null;
  let closed = false;

  try {
    const token = localStorage.getItem('auth_token') || 'dev-token';
    // Use fetch + ReadableStream for SSE since EventSource doesn't support auth headers
    const controller = new AbortController();

    fetch(url, {
      headers: { 'Authorization': `Bearer ${token}` },
      signal: controller.signal,
    }).then(async (response) => {
      if (!response.ok || !response.body) return;

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (!closed) {
        try {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          let currentEvent = '';
          for (const line of lines) {
            if (line.startsWith('event: ')) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                dispatchEvent(currentEvent, data, handlers);
              } catch {}
            }
          }
        } catch { break; }
      }
    }).catch(() => {});

    return {
      close: () => {
        closed = true;
        controller.abort();
      },
    };
  } catch {
    return { close: () => {} };
  }
}

function dispatchEvent(eventType: string, data: any, handlers: SSEEventHandler) {
  switch (eventType) {
    case 'parse.progress': handlers.onParseProgress?.(data); break;
    case 'parse.complete': handlers.onParseComplete?.(data); break;
    case 'parse.failed': handlers.onParseFailed?.(data); break;
    case 'review.progress': handlers.onReviewProgress?.(data); break;
    case 'review.log': handlers.onReviewLog?.(data); break;
    case 'review.complete': handlers.onReviewComplete?.(data); break;
    case 'review.failed': handlers.onReviewFailed?.(data); break;
    case 'review.timeout': handlers.onReviewTimeout?.(data); break;
    case 'interrupt.ready': handlers.onInterruptReady?.(data); break;
  }
}
