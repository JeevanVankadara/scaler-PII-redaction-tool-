import Icon from "./Icon";

// Fixed order, and zeroes are shown: "SSN 0" tells the reader the type is
// implemented and simply absent from this document.
const ORDER = [
  "PERSON",
  "EMAIL",
  "PHONE",
  "COMPANY",
  "ADDRESS",
  "SSN",
  "CREDIT_CARD",
  "DOB",
  "IP_ADDRESS",
];

export default function CategoryGrid({ categories }) {
  return (
    <div className="categories">
      {ORDER.map((name) => (
        <div className="category" key={name}>
          <span className="category-icon">
            <Icon name={name} />
          </span>
          <span className="category-name">{name}</span>
          <span className="category-count">{categories[name] ?? 0}</span>
        </div>
      ))}
    </div>
  );
}
