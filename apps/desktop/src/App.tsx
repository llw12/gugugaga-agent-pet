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
  const [debugOpen, setDebugOpen] = useState(false);

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
      {debugOpen && <DebugPanel current={petState} onChange={setPetState} />}
    </main>
  );
}
