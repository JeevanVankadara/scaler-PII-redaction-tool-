import { useRef, useState } from "react";
import Icon from "./Icon";

export default function UploadPanel({ status, filename, error, onSelect }) {
  const input = useRef(null);
  const [dragging, setDragging] = useState(false);
  const busy = status === "queued" || status === "running";

  function choose(files) {
    if (files && files[0]) onSelect(files[0]);
  }

  return (
    <section className="card">
      {busy ? (
        <div className="working">
          <span className="spinner" />
          <div>
            <p className="working-title">Pseudonymizing {filename}</p>
            <p className="muted">
              The document is read twice: once to collect every name, once to replace
              them. A large prospectus takes about a minute.
            </p>
          </div>
        </div>
      ) : (
        <div
          className={dragging ? "dropzone dragging" : "dropzone"}
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
          <Icon name="UPLOAD" size={26} />
          <p className="dropzone-title">Drop a .docx file here</p>
          <p className="muted">or choose one from your computer</p>
          <button className="btn primary" onClick={() => input.current.click()}>
            Select document
          </button>
          <input
            ref={input}
            type="file"
            accept=".docx"
            hidden
            onChange={(event) => choose(event.target.files)}
          />
        </div>
      )}
      {error && <p className="error">{error}</p>}
    </section>
  );
}
