// WebSocket client for /ws/analyst.
// Protocol:
//   connect(sessionId) — opens ws://localhost:8001/ws/analyst?tenantId=demo-tenant
//   send(question, sessionId) — sends {"question":"...","sessionId":"..."}
//   server streams {"type":"token","content":"..."} then {"type":"done","confidence":0.87,"citations":[...]}
//   on disconnect/error — calls onError so caller can fall back to REST

const WS_BASE = import.meta.env.VITE_REASONING_WS_URL ?? 'ws://localhost:8001'
const TENANT_ID = 'demo-tenant'

export type TokenHandler = (token: string) => void
export type DoneHandler = (confidence: number, citations: string[]) => void
export type ErrorHandler = () => void

export class AnalystWsClient {
  private ws: WebSocket | null = null

  constructor(
    private readonly onToken: TokenHandler,
    private readonly onDone: DoneHandler,
    private readonly onError: ErrorHandler,
  ) {}

  connect(sessionId: string): void {
    this.ws?.close()
    const url = `${WS_BASE}/ws/analyst?tenantId=${encodeURIComponent(TENANT_ID)}&sessionId=${encodeURIComponent(sessionId)}`
    this.ws = new WebSocket(url)

    this.ws.onmessage = (event: MessageEvent<string>) => {
      let data: { type: string; content?: string; confidence?: number; citations?: string[] }
      try {
        data = JSON.parse(event.data)
      } catch {
        return
      }
      if (data.type === 'token' && data.content != null) {
        this.onToken(data.content)
      } else if (data.type === 'done') {
        this.onDone(data.confidence ?? 0, data.citations ?? [])
      }
    }

    this.ws.onerror = () => this.onError()
    this.ws.onclose = (e: CloseEvent) => {
      if (!e.wasClean) this.onError()
    }
  }

  send(question: string, sessionId: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ question, sessionId }))
    }
  }

  isOpen(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  close(): void {
    this.ws?.close()
  }
}
