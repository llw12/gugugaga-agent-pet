export type PetState = "idle" | "thinking" | "working" | "success" | "warning" | "sleeping";

export function isPetState(value: unknown): value is PetState {
  return (
    value === "idle" ||
    value === "thinking" ||
    value === "working" ||
    value === "success" ||
    value === "warning" ||
    value === "sleeping"
  );
}
