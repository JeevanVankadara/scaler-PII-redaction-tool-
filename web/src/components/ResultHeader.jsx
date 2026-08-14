import Icon from "./Icon";

const STATS = [
  { key: "total_entities", label: "Entities replaced" },
  { key: "unique_mappings", label: "Distinct values" },
  { key: "categories_found", label: "Categories hit" },
  { key: "processing_ms", label: "Processing", format: (value) => `${(value / 1000).toFixed(1)}s` },
];

export default function ResultHeader({ job, onDownload }) {
  return (
    <section className="result-head">
      <div className="result-top">
        <div>
          <span className="chip done">
            <Icon name="CHECK" size={13} />
            Complete
          </span>
          <h2>{job.filename}</h2>
          <p className="muted small mono">{job.output_name}</p>
        </div>
        <button className="btn primary" onClick={onDownload}>
          <Icon name="DOWNLOAD" size={16} />
          Download .docx
        </button>
      </div>

      <div className="stats">
        {STATS.map((stat) => (
          <div className="stat" key={stat.key}>
            <span className="stat-value">
              {stat.format ? stat.format(job.stats[stat.key]) : job.stats[stat.key]}
            </span>
            <span className="stat-label">{stat.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
