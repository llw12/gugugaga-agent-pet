import idle from "../assets/spritesheets/idle.png";
import sleeping from "../assets/spritesheets/sleeping.png";
import success from "../assets/spritesheets/success.png";
import thinking from "../assets/spritesheets/thinking.png";
import warning from "../assets/spritesheets/warning.png";
import working from "../assets/spritesheets/working.png";
import type { PetState } from "./petState";

export interface AnimationConfig {
  src: string;
  frames: number;
  fps: number;
  loop: boolean;
  next?: PetState;
  label: string;
}

export const animationManifest: Record<PetState, AnimationConfig> = {
  idle: { src: idle, frames: 4, fps: 4, loop: true, label: "Idle" },
  thinking: { src: thinking, frames: 4, fps: 5, loop: true, label: "Thinking" },
  working: { src: working, frames: 6, fps: 8, loop: true, label: "Working" },
  success: { src: success, frames: 4, fps: 6, loop: false, next: "idle", label: "Success" },
  warning: { src: warning, frames: 4, fps: 4, loop: true, label: "Warning" },
  sleeping: { src: sleeping, frames: 4, fps: 2, loop: true, label: "Sleeping" }
};
