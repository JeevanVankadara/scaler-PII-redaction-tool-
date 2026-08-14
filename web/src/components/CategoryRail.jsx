import Icon from "./Icon";

// Fixed order, and zeroes are shown rather than hidden: "SSN 0" says the type is
// implemented and simply absent from this document.
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

const LABELS = {
  PERSON: "People",
  EMAIL: "Email addresses",
  PHONE: "Phone numbers",
  COMPANY: "Companies",
  ADDRESS: "Addresses",
  WEBSITE: "Websites",
  SSN: "SSNs",
  CREDIT_CARD: "Credit cards",
  DOB: "Dates of birth",
  IP_ADDRESS: "IP addresses",
};

export default function CategoryRail({ categories, total, active, onSelect }) {
  const highest = Math.max(1, ...Object.values(categories));

  return (
    <aside className="rail">
      <p className="rail-title">Detected by category</p>

      <button
        className={`rail-item${active === "ALL" ? " active" : ""}`}
        onClick={() => onSelect("ALL")}
      >
        <span className="rail-icon">
          <Icon name="ALL" size={15} />
        </span>
        <span className="rail-name">Everything</span>
        <span className="rail-count">{total}</span>
      </button>

      <div className="rail-divider" />

      {ORDER.map((name) => {
        const count = categories[name] ?? 0;
        return (
          <button
            key={name}
            disabled={!count}
            className={`rail-item${active === name ? " active" : ""}${count ? "" : " empty"}`}
            onClick={() => onSelect(name)}
          >
            <span className="rail-icon">
              <Icon name={name} size={15} />
            </span>
            <span className="rail-name">{LABELS[name]}</span>
            <span className="rail-count">{count}</span>
            <span className="rail-bar" style={{ width: `${(count / highest) * 100}%` }} />
          </button>
        );
      })}
    </aside>
  );
}
