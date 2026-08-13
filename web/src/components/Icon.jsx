const PATHS = {
  PERSON: "M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm0 2c-4 0-7 2-7 4v2h14v-2c0-2-3-4-7-4Z",
  EMAIL: "M3 6h18v12H3V6Zm0 0 9 7 9-7",
  PHONE: "M6 3h4l2 5-3 2a13 13 0 0 0 5 5l2-3 5 2v4a2 2 0 0 1-2 2A17 17 0 0 1 4 5a2 2 0 0 1 2-2Z",
  COMPANY: "M4 21V5h9v16M13 9h7v12M7 9h2M7 13h2M7 17h2M16 13h1M16 17h1",
  ADDRESS: "M12 21s7-6.3 7-11a7 7 0 1 0-14 0c0 4.7 7 11 7 11Zm0-8.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z",
  SSN: "M5 9h14M5 15h14M9 4 7 20M17 4l-2 16",
  CREDIT_CARD: "M3 6h18v12H3V6Zm0 4h18M6 15h4",
  DOB: "M4 6h16v15H4V6Zm0 5h16M8 3v4M16 3v4",
  IP_ADDRESS: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 0c3 3 3 15 0 18M3 12h18",
  DOWNLOAD: "M12 3v11m0 0 4-4m-4 4-4-4M4 19h16",
  REFRESH: "M4 12a8 8 0 0 1 13.7-5.7L20 8M20 4v4h-4M20 12a8 8 0 0 1-13.7 5.7L4 16M4 20v-4h4",
  CHECK: "M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm-4 9 3 3 5-6",
  SHIELD: "M12 3 5 6v6c0 4 3 7 7 9 4-2 7-5 7-9V6l-7-3Z",
  UPLOAD: "M12 17V6m0 0 4 4m-4-4-8 4M4 19h16",
};

export default function Icon({ name, size = 16 }) {
  const path = PATHS[name] || PATHS.PERSON;
  return (
    <svg
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={path} />
    </svg>
  );
}
