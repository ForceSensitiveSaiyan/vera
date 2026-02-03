import type { TokenBox } from "./ImageOverlay";

type CorrectionEditorProps = {
  token: TokenBox | null;
  value: string;
  onChange: (value: string) => void;
  onMarkReviewed: () => void;
  onUnmarkReviewed: () => void;
  onRevert: () => void;
  disabled?: boolean;
  isReviewed?: boolean;
};

export function CorrectionEditor({
  token,
  value,
  onChange,
  onMarkReviewed,
  onUnmarkReviewed,
  onRevert,
  disabled = false,
  isReviewed = false,
}: CorrectionEditorProps) {
  if (!token) {
    return <div className="form-hint">Select a flagged token to review</div>;
  }

  return (
    <div className="vera-stack">
      <div className="form-group">
        <span className="form-label">Original</span>
        <div>{token.text || "(empty)"}</div>
      </div>
      <label className="form-group">
        <span className="form-label">Correction</span>
        <input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="form-input"
          disabled={disabled}
        />
      </label>
      <div className="form-row">
        {isReviewed ? (
          <button type="button" onClick={onUnmarkReviewed} className="btn btn-secondary" disabled={disabled}>
            Mark unreviewed
          </button>
        ) : (
          <button type="button" onClick={onMarkReviewed} className="btn btn-secondary" disabled={disabled}>
            Mark reviewed
          </button>
        )}
        <button type="button" onClick={onRevert} className="btn btn-secondary" disabled={disabled}>
          Revert
        </button>
      </div>
    </div>
  );
}
