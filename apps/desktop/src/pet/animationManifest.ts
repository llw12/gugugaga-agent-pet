import idle0 from "../assets/pet/idle/000.png";
import idle1 from "../assets/pet/idle/001.png";
import idle2 from "../assets/pet/idle/002.png";
import idle3 from "../assets/pet/idle/003.png";
import sleeping0 from "../assets/pet/sleeping/000.png";
import sleeping1 from "../assets/pet/sleeping/001.png";
import sleeping2 from "../assets/pet/sleeping/002.png";
import sleeping3 from "../assets/pet/sleeping/003.png";
import success0 from "../assets/pet/success/000.png";
import success1 from "../assets/pet/success/001.png";
import success2 from "../assets/pet/success/002.png";
import success3 from "../assets/pet/success/003.png";
import thinking0 from "../assets/pet/thinking/000.png";
import thinking1 from "../assets/pet/thinking/001.png";
import thinking2 from "../assets/pet/thinking/002.png";
import thinking3 from "../assets/pet/thinking/003.png";
import warning0 from "../assets/pet/warning/000.png";
import warning1 from "../assets/pet/warning/001.png";
import warning2 from "../assets/pet/warning/002.png";
import warning3 from "../assets/pet/warning/003.png";
import working0 from "../assets/pet/working/000.png";
import working1 from "../assets/pet/working/001.png";
import working2 from "../assets/pet/working/002.png";
import working3 from "../assets/pet/working/003.png";
import working4 from "../assets/pet/working/004.png";
import working5 from "../assets/pet/working/005.png";
import type { PetState } from "./petState";

export interface AnimationConfig {
  frameUrls: string[];
  fps: number;
  loop: boolean;
  next?: PetState;
  label: string;
}

export const animationManifest: Record<PetState, AnimationConfig> = {
  idle: { frameUrls: [idle0, idle1, idle2, idle3], fps: 4, loop: true, label: "Idle" },
  thinking: { frameUrls: [thinking0, thinking1, thinking2, thinking3], fps: 5, loop: true, label: "Thinking" },
  working: {
    frameUrls: [working0, working1, working2, working3, working4, working5],
    fps: 8,
    loop: true,
    label: "Working"
  },
  success: {
    frameUrls: [success0, success1, success2, success3],
    fps: 6,
    loop: false,
    next: "idle",
    label: "Success"
  },
  warning: { frameUrls: [warning0, warning1, warning2, warning3], fps: 4, loop: true, label: "Warning" },
  sleeping: { frameUrls: [sleeping0, sleeping1, sleeping2, sleeping3], fps: 2, loop: true, label: "Sleeping" }
};
