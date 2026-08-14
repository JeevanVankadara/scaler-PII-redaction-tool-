import { useRef, useState } from "react";
import Icon from "./Icon";

const POINTS = [
  { icon: "LAYERS", title: "Ten PII types", body: "Names, companies and addresses from a model; the rest by pattern." },
  { icon: "LOCK", title: "Linked identities", body: "A person and their email address resolve to the same fake identity." },
  { icon: "ZAP", title: "Shape preserved", body: "Numbers, dates and formatting survive, so the document still reads." },
];

export default function Hero({ error, onSelect }) {
  const input = useRef(null);
  const [dragging, setDragging] = useState(false);

  function choose(files) {
    if (files && files[0]) onSelect(files[0]);
  }

  return (
    <div className="hero">
      <h1>
        Strip personal data from a <span className="gradient">Word document</span>
      </h1>
      <p className="lede">
        Detects names, contact details, companies and addresses in a .docx and replaces
        them with consistent synthetic alternatives. The layout comes out unchanged.
      </p>

      <div
        className={dragging ? "drop dragging" : "drop"}
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragging(false);
          choose(event.dataTransfer.files);
        }}
      >
        <span className="drop-icon">
          <Icon name="UPLOAD" size={22} />
        </span>
        <p className="drop-title">Drop a .docx file here</p>
        <p className="muted small">Nothing is stored. Files are deleted after an hour.</p>
        <button className="btn primary" onClick={() => input.current.click()}>
          Choose a document
        </button>
        <input
          ref={input}
          type="file"
          accept=".docx"
          hidden
          onChange={(event) => choose(event.target.files)}
        />
      </div>

      {error && <p className="error">{error}</p>}

      <div className="points">
        {POINTS.map((point) => (
          <div className="point" key={point.title}>
            <span className="point-icon">
              <Icon name={point.icon} size={16} />
            </span>
            <div>
              <strong>{point.title}</strong>
              <p className="muted small">{point.body}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
