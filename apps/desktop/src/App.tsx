import { useCallback, useEffect, useMemo, useState } from "react";
import { Bug, GripHorizontal, MessageCircle, X } from "lucide-react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import type { ChatMessage, ServerEvent } from "./api/types";
import { AgentWsClient } from "./api/wsClient";
import { ChatPanel } from "./components/ChatPanel";
import { DebugPanel } from "./components/DebugPanel";
import { PetSprite } from "./pet/PetSprite";
import { isPetState, type PetState } from "./pet/petState";

function isTauriRuntime() {
  return "__TAURI_INTERNALS__" in window;
}

export default function App() {
  const wsClient = useMemo(() => new AgentWsClient(), []);
  const [petState, setPetState] = useState<PetState>("idle");
  const [debugOpen, setDebugOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(true);
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: "phase-2-ready", role: "system", text: "Phase 2 mock 后端接入中。" }
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
      if (event.type === "final") {
        if (event.payload?.text) {
          appendMessage("system", event.payload.text);
        }
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
      {debugOpen && <DebugPanel current={petState} onChange={setPetState} />}
    </main>
  );
}
