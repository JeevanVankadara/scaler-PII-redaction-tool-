import { useMemo, useState } from "react";
import Icon from "./Icon";

export default function ValuesTable({ rows, type }) {
  const [query, setQuery] = useState("");

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
    <section className="panel">
      <div className="panel-head">
        <div>
          <h3>{type === "ALL" ? "Everything that was replaced" : type}</h3>
          <p className="muted small">
            {visible.length} of {rows.length} distinct values
          </p>
        </div>
        <label className="search">
          <Icon name="SEARCH" size={15} />
          <input
            placeholder="Search a name, address, anything"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
      </div>

      <p className="notice">
        <Icon name="LOCK" size={14} />
        The left column is unredacted text from your document. Anyone who can read this
        can reverse the pseudonymization.
      </p>

      <div className="rows">
        {visible.map((row, index) => (
          <div className="row" key={`${row.type}-${row.original}-${index}`}>
            <span className="tag">{row.type}</span>
            <span className="from mono">{row.original}</span>
            <Icon name="ARROW" size={15} className="arrow" />
            <span className="to mono">{row.replacement}</span>
          </div>
        ))}
        {visible.length === 0 && <p className="empty-note muted">Nothing matches that filter.</p>}
      </div>
    </section>
  );
}
