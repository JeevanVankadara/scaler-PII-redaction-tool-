import { useCallback, useEffect, useRef, useState } from "react";
import { createJob, downloadDocx, errorMessage, readJob, readMapping } from "./api";
import CategoryRail from "./components/CategoryRail";
import Hero from "./components/Hero";
import Processing from "./components/Processing";
import ResultHeader from "./components/ResultHeader";
import TopBar from "./components/TopBar";
import ValuesTable from "./components/ValuesTable";

const POLL_MS = 1500;

export default function App() {
  const [job, setJob] = useState(null);
  const [mapping, setMapping] = useState([]);
  const [type, setType] = useState("ALL");
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
    setType("ALL");
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
          setJob(null);
          setError(latest.error);
        }
      } catch (problem) {
        stop();
        setJob(null);
        setError(errorMessage(problem));
      }
    }, POLL_MS);
  }

  function reset() {
    stop();
    setJob(null);
    setMapping([]);
    setType("ALL");
    setError("");
  }

  const busy = job?.status === "queued" || job?.status === "running";
  const done = job?.status === "done";

  return (
    <div className="app">
      <TopBar job={job} onReset={reset} />

      <main className="main">
        {!job && <Hero error={error} onSelect={upload} />}
        {busy && <Processing filename={job.filename} />}

        {done && (
          <div className="result">
            <ResultHeader job={job} onDownload={() => downloadDocx(job.id, job.output_name)} />
            <div className="split">
              <CategoryRail
                categories={job.stats.categories}
                total={job.stats.total_entities}
                active={type}
                onSelect={setType}
              />
              <ValuesTable rows={mapping} type={type} />
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
