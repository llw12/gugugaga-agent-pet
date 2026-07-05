import type { ClientEvent, ServerEvent } from "./types";

type EventListener = (event: ServerEvent) => void;
type StatusListener = (connected: boolean) => void;

export class AgentWsClient {
  private socket: WebSocket | null = null;
  private eventListeners = new Set<EventListener>();
  private statusListeners = new Set<StatusListener>();
  private reconnectTimer: number | null = null;
  private stopped = false;

  constructor(private readonly url = "ws://127.0.0.1:8765/ws") {}

  connect() {
    if (this.socket && this.socket.readyState <= WebSocket.OPEN) return;

    this.stopped = false;
    this.socket = new WebSocket(this.url);

    this.socket.addEventListener("open", () => this.emitStatus(true));
    this.socket.addEventListener("message", (message) => {
      try {
        this.emitEvent(JSON.parse(message.data) as ServerEvent);
      } catch {
        this.emitEvent({
          type: "assistant_message",
          payload: { text: "收到了一条无法解析的后端消息。" }
        });
      }
    });
    this.socket.addEventListener("close", () => {
      this.emitStatus(false);
      if (!this.stopped) this.scheduleReconnect();
    });
    this.socket.addEventListener("error", () => {
      this.emitStatus(false);
    });
  }

  send(event: ClientEvent) {
    if (this.socket?.readyState !== WebSocket.OPEN) return false;
    this.socket.send(JSON.stringify(event));
    return true;
  }

  stop() {
    this.stopped = true;
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.socket?.close();
  }

  onEvent(listener: EventListener) {
    this.eventListeners.add(listener);
    return () => this.eventListeners.delete(listener);
  }

  onStatus(listener: StatusListener) {
    this.statusListeners.add(listener);
    return () => this.statusListeners.delete(listener);
  }

  private scheduleReconnect() {
    if (this.reconnectTimer !== null) return;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, 2500);
  }

  private emitEvent(event: ServerEvent) {
    this.eventListeners.forEach((listener) => listener(event));
  }

  private emitStatus(connected: boolean) {
    this.statusListeners.forEach((listener) => listener(connected));
  }
}
