import { FormEvent, useState } from "react";
import { Send, X } from "lucide-react";
import type { ChatMessage } from "../api/types";

interface ChatPanelProps {
  connected: boolean;
  messages: ChatMessage[];
  onSend: (text: string) => void;
  onClose: () => void;
}

export function ChatPanel({ connected, messages, onSend, onClose }: ChatPanelProps) {
  const [text, setText] = useState("");

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const value = text.trim();
    if (!value) return;
    onSend(value);
    setText("");
  };

  return (
    <section className="chatPanel" aria-label="Agent chat">
      <header className="chatHeader">
        <div>
          <strong>Phase 4 Chat</strong>
          <span className={connected ? "connectionBadge connectionOnline" : "connectionBadge"}>
            {connected ? "connected" : "Agent 后端未连接"}
          </span>
        </div>
        <button className="panelIconButton" type="button" aria-label="Close chat" onClick={onClose}>
          <X size={16} />
        </button>
      </header>

      <div className="messageList">
        {messages.length === 0 && <p className="emptyChat">输入一句话，测试 Phase 4 WebSocket 和安全确认骨架。</p>}
        {messages.map((message) => (
          <div className={`chatBubble chatBubble-${message.role}`} key={message.id}>
            {message.text}
          </div>
        ))}
      </div>

      <form className="chatForm" onSubmit={submit}>
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="和咕咕嘎嘎说话"
          aria-label="Message"
        />
        <button className="sendButton" type="submit" aria-label="Send message">
          <Send size={16} />
          <span>发送</span>
        </button>
      </form>
    </section>
  );
}
