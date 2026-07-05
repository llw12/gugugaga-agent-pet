import type { PetState } from "../pet/petState";

export type MessageRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  text: string;
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
