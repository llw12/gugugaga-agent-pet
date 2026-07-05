import { animationManifest } from "../pet/animationManifest";
import type { PetState } from "../pet/petState";

interface DebugPanelProps {
  current: PetState;
  onChange: (state: PetState) => void;
}

export function DebugPanel({ current, onChange }: DebugPanelProps) {
  return (
    <section className="debugPanel" aria-label="Pet animation debug controls">
      {(Object.keys(animationManifest) as PetState[]).map((state) => (
        <button
          className={state === current ? "debugButton debugButtonActive" : "debugButton"}
          key={state}
          type="button"
          onClick={() => onChange(state)}
          title={`Switch to ${state}`}
        >
          {state}
        </button>
      ))}
    </section>
  );
}
