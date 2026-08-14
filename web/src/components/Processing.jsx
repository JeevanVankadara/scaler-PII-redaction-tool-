import { useEffect, useState } from "react";
import Icon from "./Icon";

/**
 * There is no real progress to report: the work happens inside two passes over
 * the document and neither reports a percentage. So this shows elapsed time and
 * an indeterminate bar rather than inventing a number that would be a guess.
 */
export default function Processing({ filename }) {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setSeconds((value) => value + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="hero">
      <div className="processing">
        <span className="file-chip">
          <Icon name="FILE" size={15} />
          {filename}
        </span>

        <h2>Working through the document</h2>
        <p className="muted">
          It is read twice: once to collect every name and company, then again to
          replace them. A large prospectus takes about a minute.
        </p>

        <div className="track">
          <span className="track-fill" />
        </div>
        <p className="muted small mono">{seconds}s elapsed</p>
      </div>
    </div>
  );
}
