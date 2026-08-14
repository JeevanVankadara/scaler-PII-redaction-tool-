import Icon from "./Icon";

export default function TopBar({ job, onReset }) {
  return (
    <header className="topbar">
      <div className="brand">
        <span className="mark">
          <Icon name="SHIELD" size={17} />
        </span>
        <span className="brand-text">
          <strong>PII Pseudonymization</strong>
          <em>Enterprise Security &amp; Privacy Engine</em>
        </span>
      </div>

      {job?.status === "done" && (
        <button className="btn ghost" onClick={onReset}>
          <Icon name="REFRESH" size={15} />
          New document
        </button>
      )}
    </header>
  );
}
