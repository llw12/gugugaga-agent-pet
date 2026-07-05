import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, Bug, GripHorizontal, MessageCircle, X } from "lucide-react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import type { ApprovalRequest, ChatMessage, ServerEvent } from "./api/types";
import { AgentWsClient } from "./api/wsClient";
import { ChatPanel } from "./components/ChatPanel";
import { ConfirmDialog } from "./components/ConfirmDialog";
import { DebugPanel } from "./components/DebugPanel";
import { StatusPanel } from "./components/StatusPanel";
import { PetSprite } from "./pet/PetSprite";
import { isPetState, type PetState } from "./pet/petState";

function isTauriRuntime() {
  return "__TAURI_INTERNALS__" in window;
}

export default function App() {
  const wsClient = useMemo(() => new AgentWsClient(), []);
  const [petState, setPetState] = useState<PetState>("idle");
  const [debugOpen, setDebugOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);
  const [statusOpen, setStatusOpen] = useState(false);
  const [connected, setConnected] = useState(false);
  const [approvalRequest, setApprovalRequest] = useState<ApprovalRequest | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: "phase-3-ready", role: "system", text: "Phase 3 mock 后端接入中。" }
  ]);

  const handleAnimationComplete = useCallback((next?: PetState) => {
    setPetState(next ?? "idle");
  }, []);

  const closeWindow = async () => {
    if (isTauriRuntime()) {
      await getCurrentWindow().close();
    }
  };

  const appendMessage = useCallback((role: ChatMessage["role"], text: string) => {
    setMessages((current) => [...current, { id: crypto.randomUUID(), role, text }]);
  }, []);

  useEffect(() => {
    const offStatus = wsClient.onStatus((online) => {
      setConnected(online);
      if (!online) {
        setPetState("idle");
      }
    });

    const offEvent = wsClient.onEvent((event: ServerEvent) => {
      if (event.type === "pet_state" && isPetState(event.payload.state)) {
        setPetState(event.payload.state);
        return;
      }
      if (event.type === "assistant_message") {
        appendMessage("assistant", event.payload.text);
        setChatOpen(true);
        return;
      }
      if (event.type === "approval_required") {
        setApprovalRequest(event.payload);
        setPetState("warning");
        setChatOpen(true);
        appendMessage("system", `收到确认请求：${event.payload.summary}`);
        return;
      }
      if (event.type === "final" && event.payload?.text) {
        appendMessage("system", event.payload.text);
      }
    });

    wsClient.connect();

    return () => {
      offStatus();
      offEvent();
      wsClient.stop();
    };
  }, [appendMessage, wsClient]);

  const sendMessage = (text: string) => {
    appendMessage("user", text);
    setChatOpen(true);
    const sent = wsClient.send({ type: "user_message", payload: { text } });
    if (!sent) {
      setPetState("idle");
      appendMessage("system", "Agent 后端未连接");
    }
  };

  const decideApproval = (approved: boolean) => {
    if (!approvalRequest) return;
    const sent = wsClient.send({
      type: "approval_result",
      payload: { request_id: approvalRequest.request_id, approved }
    });
    appendMessage("system", approved ? "已发送确认结果：同意。" : "已发送确认结果：取消。");
    if (!sent) {
      appendMessage("system", "Agent 后端未连接，确认结果未发送。");
    }
    setApprovalRequest(null);
  };

  return (
    <main className="appShell">
      <div className="dragRegion" data-tauri-drag-region title="Drag Gugugaga">
        <PetSprite state={petState} onComplete={handleAnimationComplete} />
      </div>

      <nav className="toolbar" aria-label="Desktop pet controls">
        <button className="iconButton" type="button" aria-label="Drag window" title="Drag window" data-tauri-drag-region>
          <GripHorizontal size={18} />
        </button>
        <button
          className="iconButton"
          type="button"
          aria-label="Toggle chat"
          title="Toggle chat"
          onClick={() => setChatOpen((open) => !open)}
        >
          <MessageCircle size={18} />
        </button>
        <button
          className="iconButton"
          type="button"
          aria-label="Toggle system status"
          title="Toggle system status"
          onClick={() => setStatusOpen((open) => !open)}
        >
          <Activity size={18} />
        </button>
        <button
          className="iconButton"
          type="button"
          aria-label="Toggle debug panel"
          title="Toggle debug panel"
          onClick={() => setDebugOpen((open) => !open)}
        >
          <Bug size={18} />
        </button>
        <button className="iconButton" type="button" aria-label="Close" title="Close" onClick={() => void closeWindow()}>
          <X size={18} />
        </button>
      </nav>

      <div className="stateBadge">{petState}</div>
      {chatOpen && <ChatPanel connected={connected} messages={messages} onSend={sendMessage} onClose={() => setChatOpen(false)} />}
      {statusOpen && <StatusPanel onClose={() => setStatusOpen(false)} />}
      {debugOpen && <DebugPanel current={petState} onChange={setPetState} />}
      {approvalRequest && <ConfirmDialog request={approvalRequest} onDecision={decideApproval} />}
    </main>
  );
}
