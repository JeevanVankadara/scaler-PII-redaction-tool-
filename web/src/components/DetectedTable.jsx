import { useMemo, useState } from "react";
import { ORDER } from "./Analytics";

export default function DetectedTable({ rows, type, onType }) {
  const [query, setQuery] = useState("");

  const present = useMemo(() => {
    const seen = new Set(rows.map((row) => row.type));
    return ["ALL", ...ORDER.filter((name) => seen.has(name))];
  }, [rows]);

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return rows.filter(
      (row) =>
        (type === "ALL" || row.type === type) &&
        (!needle ||
          row.original.toLowerCase().includes(needle) ||
          row.replacement.toLowerCase().includes(needle))
    );
  }, [rows, query, type]);

  return (
    <section className="card">
      <h2 className="section-title first">Everything that was detected</h2>
      <p className="warning">
        The left column is the original text from your document. Anyone who can read
        this table can reverse the pseudonymization.
      </p>

      <div className="filters">
        <input
          className="input"
          placeholder="Search names, addresses, anything"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <select
          className="input select"
          value={type}
          onChange={(event) => onType(event.target.value)}
        >
          {present.map((name) => (
            <option key={name} value={name}>
              {name === "ALL" ? "All categories" : name}
            </option>
          ))}
        </select>
        <span className="muted">
          showing {visible.length} of {rows.length}
        </span>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Category</th>
              <th>Original value</th>
              <th>Replaced with</th>
            </tr>
          </thead>
          <tbody>
            {visible.map((row, index) => (
              <tr key={`${row.type}-${row.original}-${index}`}>
                <td>
                  <span className="pill">{row.type}</span>
                </td>
                <td className="original">{row.original}</td>
                <td className="replacement">{row.replacement}</td>
              </tr>
            ))}
            {visible.length === 0 && (
              <tr>
                <td colSpan="3" className="muted center">
                  Nothing matches that filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
