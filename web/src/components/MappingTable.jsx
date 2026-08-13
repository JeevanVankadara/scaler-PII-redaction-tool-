import { useMemo, useState } from "react";

export default function MappingTable({ rows }) {
  const [query, setQuery] = useState("");
  const [type, setType] = useState("ALL");

  const types = useMemo(
    () => ["ALL", ...Array.from(new Set(rows.map((row) => row.type))).sort()],
    [rows]
  );

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
      <h2 className="section-title">Replacement Mapping</h2>
      <p className="warning">
        This table contains the original values from your document. Anyone who can
        read it can reverse the pseudonymization.
      </p>

      <div className="filters">
        <input
          className="input"
          placeholder="Search originals or replacements"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
        <select
          className="input select"
          value={type}
          onChange={(event) => setType(event.target.value)}
        >
          {types.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
        <span className="muted">
          {visible.length} of {rows.length}
        </span>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Original</th>
              <th>Replacement</th>
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
