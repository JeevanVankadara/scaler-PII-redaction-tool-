const TILES = [
  { key: "total_entities", label: "TOTAL PII ENTITIES", tone: "indigo" },
  { key: "unique_mappings", label: "UNIQUE MAPPINGS", tone: "indigo" },
  { key: "categories_found", label: "CATEGORIES FOUND", tone: "green" },
  { key: "processing_ms", label: "PROCESSING TIME", tone: "dark", suffix: " ms" },
];

export default function SummaryCards({ stats }) {
  return (
    <div className="summary">
      {TILES.map((tile) => (
        <div className="tile" key={tile.key}>
          <p className={`tile-value ${tile.tone}`}>
            {stats[tile.key]}
            {tile.suffix || ""}
          </p>
          <p className="tile-label">{tile.label}</p>
        </div>
      ))}
    </div>
  );
}
