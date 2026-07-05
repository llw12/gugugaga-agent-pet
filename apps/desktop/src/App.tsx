import { useCallback, useState } from "react";
import { Bug, GripHorizontal, X } from "lucide-react";
import { getCurrentWindow } from "@tauri-apps/api/window";
import { DebugPanel } from "./components/DebugPanel";
import { PetSprite } from "./pet/PetSprite";
import type { PetState } from "./pet/petState";

function isTauriRuntime() {
  return "__TAURI_INTERNALS__" in window;
}

export default function App() {
  const [petState, setPetState] = useState<PetState>("idle");
  const [debugOpen, setDebugOpen] = useState(true);

  const handleAnimationComplete = useCallback((next?: PetState) => {
    setPetState(next ?? "idle");
  }, []);

  const closeWindow = async () => {
    if (isTauriRuntime()) {
      await getCurrentWindow().close();
    }
  };

  return (
    <main className="appShell">
      <div className="dragRegion" data-tauri-drag-region title="拖动咕咕嘎嘎">
        <PetSprite state={petState} onComplete={handleAnimationComplete} />
      </div>

      <nav className="toolbar" aria-label="Desktop pet controls">
        <button
          className="iconButton"
          type="button"
          aria-label="拖动窗口"
          title="拖动窗口"
          data-tauri-drag-region
        >
          <GripHorizontal size={18} />
        </button>
        <button
          className="iconButton"
          type="button"
          aria-label="切换调试面板"
          title="切换调试面板"
          onClick={() => setDebugOpen((open) => !open)}
        >
          <Bug size={18} />
        </button>
        <button className="iconButton" type="button" aria-label="退出" title="退出" onClick={() => void closeWindow()}>
          <X size={18} />
        </button>
      </nav>

      <div className="stateBadge">{petState}</div>
      {debugOpen && <DebugPanel current={petState} onChange={setPetState} />}
    </main>
  );
}
