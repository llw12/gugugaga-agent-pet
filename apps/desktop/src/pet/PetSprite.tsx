import { useEffect, useState } from "react";
import { animationManifest } from "./animationManifest";
import type { PetState } from "./petState";

interface PetSpriteProps {
  state: PetState;
  onComplete?: (next?: PetState) => void;
}

export function PetSprite({ state, onComplete }: PetSpriteProps) {
  const config = animationManifest[state];
  const [frameIndex, setFrameIndex] = useState(0);

  useEffect(() => {
    setFrameIndex(0);
  }, [state]);

  useEffect(() => {
    let rafId = 0;
    let lastFrameAt = performance.now();
    let completed = false;
    const frameMs = 1000 / config.fps;
    const frameCount = config.frameUrls.length;

    const tick = (now: number) => {
      if (now - lastFrameAt >= frameMs) {
        lastFrameAt = now;
        setFrameIndex((current) => {
          const next = current + 1;
          if (next < frameCount) return next;
          if (config.loop) return 0;
          if (!completed) {
            completed = true;
            window.setTimeout(() => onComplete?.(config.next), 0);
          }
          return Math.max(frameCount - 1, 0);
        });
      }
      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [config, onComplete]);

  const currentFrame = config.frameUrls[Math.min(frameIndex, config.frameUrls.length - 1)];

  return (
    <div className="petSprite" aria-label={`Gugugaga ${config.label}`}>
      <img className="petSpriteImage" src={currentFrame} alt="" draggable={false} />
    </div>
  );
}
