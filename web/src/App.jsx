import { useCallback, useEffect, useRef, useState } from "react";
import { createJob, downloadDocx, errorMessage, readJob, readMapping } from "./api";
import CategoryGrid from "./components/CategoryGrid";
import Icon from "./components/Icon";
import MappingTable from "./components/MappingTable";
import SummaryCards from "./components/SummaryCards";
import UploadPanel from "./components/UploadPanel";

const POLL_MS = 1500;

export default function App() {
  const [job, setJob] = useState(null);
  const [mapping, setMapping] = useState([]);
  const [error, setError] = useState("");
  const timer = useRef(null);

  const stop = useCallback(() => {
    if (timer.current) {
      clearInterval(timer.current);
      timer.current = null;
    }
  }, []);

  useEffect(() => stop, [stop]);

  async function upload(file) {
    setError("");
    setMapping([]);
    try {
      const created = await createJob(file);
      setJob(created);
      poll(created.id);
    } catch (problem) {
      setError(errorMessage(problem));
    }
  }

  function poll(id) {
    stop();
    timer.current = setInterval(async () => {
      try {
        const latest = await readJob(id);
        setJob(latest);
        if (latest.status === "done") {
          stop();
          const { rows } = await readMapping(id);
          setMapping(rows);
        } else if (latest.status === "error") {
          stop();
          setError(latest.error);
        }
      } catch (problem) {
        stop();
        setError(errorMessage(problem));
      }
    }, POLL_MS);
  }

  function reset() {
    stop();
    setJob(null);
    setMapping([]);
    setError("");
  }

  const done = job && job.status === "done";

  return (
    <div className="page">
      <header className="header">
        <span className="badge">
          <Icon name="SHIELD" size={14} />
          Enterprise Security &amp; Privacy Engine
        </span>
        <h1>PII Pseudonymization Tool</h1>
        <p className="lede">
          Automatically detect sensitive personal information in Microsoft Word (.docx)
          documents and replace it with privacy-preserving synthetic alternatives.
        </p>
      </header>

      {!done && (
        <UploadPanel
          status={job?.status}
          filename={job?.filename}
          error={error}
          onSelect={upload}
        />
      )}

      {done && (
        <>
          <section className="card">
            <span className="badge success">
              <Icon name="CHECK" size={14} />
              Pseudonymization Complete
            </span>

            <div className="summary-head">
              <div>
                <h2 className="title">Document Transformation Summary</h2>
                <p className="muted">
                  Output document: <strong className="link">{job.output_name}</strong>
                </p>
              </div>
              <div className="actions">
                <button
                  className="btn primary"
                  onClick={() => downloadDocx(job.id, job.output_name)}
                >
                  <Icon name="DOWNLOAD" size={16} />
                  Download Pseudonymized DOCX
                </button>
                <button className="btn" onClick={reset}>
                  <Icon name="REFRESH" size={16} />
                  Process Another Document
                </button>
              </div>
            </div>

            <hr className="rule" />

            <SummaryCards stats={job.stats} />

            <h3 className="section-title">PII Detected by Category</h3>
            <CategoryGrid categories={job.stats.categories} />
          </section>

          <MappingTable rows={mapping} />
        </>
      )}
    </div>
  );
}
