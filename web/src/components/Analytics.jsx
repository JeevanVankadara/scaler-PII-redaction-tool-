import Icon from "./Icon";

const TILES = [
  { key: "total_entities", label: "TOTAL PII ENTITIES", tone: "indigo" },
  { key: "unique_mappings", label: "UNIQUE MAPPINGS", tone: "indigo" },
  { key: "categories_found", label: "CATEGORIES FOUND", tone: "green" },
  { key: "processing_ms", label: "PROCESSING TIME", tone: "dark", suffix: " ms" },
];

// Fixed order, and zeroes are shown: "SSN 0" says the type is implemented and
// simply absent from this document.
export const ORDER = [
  "PERSON",
  "EMAIL",
  "PHONE",
  "COMPANY",
  "ADDRESS",
  "WEBSITE",
  "SSN",
  "CREDIT_CARD",
  "DOB",
  "IP_ADDRESS",
];

export default function Analytics({ stats, active, onSelect }) {
  const total = stats.total_entities || 1;
  return (
    <>
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

      <h3 className="section-title">PII Detected by Category</h3>
      <div className="categories">
        {ORDER.map((name) => {
          const count = stats.categories[name] ?? 0;
          return (
            <button
              key={name}
              className={`category${active === name ? " active" : ""}${count ? "" : " empty"}`}
              onClick={() => onSelect(active === name ? "ALL" : name)}
              title={count ? `Show the ${count} ${name} values` : "None found"}
            >
              <span className="category-icon">
                <Icon name={name} />
              </span>
              <span className="category-name">{name}</span>
              <span className="category-count">{count}</span>
              <span className="bar" style={{ width: `${(count / total) * 100}%` }} />
            </button>
          );
        })}
      </div>
    </>
  );
}
