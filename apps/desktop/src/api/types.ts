import type { PetState } from "../pet/petState";

export type MessageRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  text: string;
}

export interface SystemOverview {
  cpu_percent: number;
  memory: {
    total: number;
    available: number;
    used: number;
    percent: number;
  };
  disk: {
    path: string;
    total: number;
    used: number;
    free: number;
    percent: number;
  };
}

export interface ProcessInfo {
  pid: number;
  name: string;
  cpu_percent: number;
  memory_percent: number;
}

export interface ProcessTopResponse {
  processes: ProcessInfo[];
}

export type ClientEvent = {
  type: "user_message";
  payload: {
    text: string;
  };
};

export type ServerEvent =
  | {
      type: "pet_state";
      payload: {
        state: PetState;
      };
    }
  | {
      type: "assistant_message";
      payload: {
        text: string;
      };
    }
  | {
      type: "final";
      payload?: {
        text?: string;
      };
    };
