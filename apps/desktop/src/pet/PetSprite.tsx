import { useEffect, useMemo, useState } from "react";
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

    const tick = (now: number) => {
      if (now - lastFrameAt >= frameMs) {
        lastFrameAt = now;
        setFrameIndex((current) => {
          const next = current + 1;
          if (next < config.frames) return next;
          if (config.loop) return 0;
          if (!completed) {
            completed = true;
            window.setTimeout(() => onComplete?.(config.next), 0);
          }
          return config.frames - 1;
        });
      }
      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
  }, [config, onComplete]);

  const style = useMemo(() => {
    const position = config.frames <= 1 ? 0 : (frameIndex / (config.frames - 1)) * 100;
    return {
      backgroundImage: `url(${config.src})`,
      backgroundPosition: `${position}% center`,
      backgroundSize: `${config.frames * 100}% 100%`
    };
  }, [config, frameIndex]);

  return <div className="petSprite" style={style} aria-label={`Gugugaga ${config.label}`} />;
}
