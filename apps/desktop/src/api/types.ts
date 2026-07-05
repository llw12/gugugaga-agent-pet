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
} | {
  type: "approval_result";
  payload: {
    request_id: string;
    approved: boolean;
  };
};

export interface ApprovalRequest {
  request_id: string;
  title: string;
  risk_level: "safe" | "low" | "medium" | "high" | "blocked" | string;
  tool: string;
  summary: string;
  detail: string;
}

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
      type: "approval_required";
      payload: ApprovalRequest;
    }
  | {
      type: "final";
      payload?: {
        text?: string;
      };
    };
