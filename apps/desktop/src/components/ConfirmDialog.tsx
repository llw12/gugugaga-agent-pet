import type { ApprovalRequest } from "../api/types";

interface ConfirmDialogProps {
  request: ApprovalRequest;
  onDecision: (approved: boolean) => void;
}

export function ConfirmDialog({ request, onDecision }: ConfirmDialogProps) {
  return (
    <div className="dialogBackdrop" role="presentation">
      <section className="confirmDialog" role="dialog" aria-modal="true" aria-labelledby="approval-title">
        <h2 id="approval-title">{request.title}</h2>
        <dl className="confirmMeta">
          <div>
            <dt>Tool</dt>
            <dd>{request.tool}</dd>
          </div>
          <div>
            <dt>Risk</dt>
            <dd>{request.risk_level}</dd>
          </div>
        </dl>
        <p className="confirmSummary">{request.summary}</p>
        <p className="confirmDetail">{request.detail}</p>
        <div className="dialogActions">
          <button className="secondaryButton" type="button" onClick={() => onDecision(false)}>
            取消
          </button>
          <button className="dangerButton" type="button" onClick={() => onDecision(true)}>
            确认
          </button>
        </div>
      </section>
    </div>
  );
}
