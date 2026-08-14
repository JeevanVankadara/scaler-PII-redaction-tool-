"""Word lists that turn raw spaCy output into something usable on a prospectus.

Every entry here was added because the model actually produced it on the source
document — see the notes in the README rather than treating these as generic.
"""

import re

# Document vocabulary. An entity built entirely from these words is offer
# jargon, not a name: "Equity Shares", "the Offer Price", "Anchor Investors".
JARGON = {
    "account", "acknowledgement", "agent", "agents", "allotment", "allotted",
    "allottee", "allottees", "amount", "anchor", "applicant", "applicants",
    "application", "approval", "arrangement", "articles", "association",
    "auditor", "auditors", "banker", "bankers", "basis", "bid", "bidder",
    "bidders", "bidding", "bids", "board", "book", "bracket", "branch", "brlm",
    "brlms", "cagr", "cap", "capital", "cash", "category", "circular",
    "closing", "committee", "company", "consideration", "corrigenda",
    "criteria", "cut", "date", "deed", "defaulter", "depository", "designated",
    "director", "directors", "documents", "dp", "draft", "eligible", "equity",
    # "financial" is deliberately absent: it blocked the newspaper FINANCIAL
    # EXPRESS, and "Financial Statements" is already caught by "statements".
    "escrow", "floor", "form", "fresh", "fund", "funds", "gaap",
    "group", "herring", "holder", "holders", "id", "individual",
    "institutional", "instruments", "intermediaries", "investor", "investors",
    "issue", "issuer", "key", "kmp", "letter", "listing", "lot", "managerial",
    "management", "margin", "market", "materiality", "measures", "meeting",
    "member", "members", "memorandum", "minimum", "mutual", "net", "non",
    "note", "objects", "offer", "offered", "opening", "operational", "option",
    "parents", "participant", "pat", "period", "personnel", "policy",
    "portion", "post", "pre", "price", "pricing", "proceeds", "promoter",
    "promoters", "proposed", "prospectus", "public", "qib", "qibs", "rate",
    "receipt", "red", "reference", "registrar", "regulations", "report",
    "reserved", "restated", "retail", "revision", "risk", "sale", "schedule",
    "scheme", "securities", "selling", "share", "shareholder", "shareholders",
    "shares", "slip", "sponsor", "statements", "stock", "subscription",
    "syndicate", "thereto", "trading", "transfer", "trusts", "underwriter",
    "underwriters", "underwriting", "upi", "website", "wilful", "working",
    # Second pass: acronyms and headings the model filed as organisations.
    "agency", "aif", "as", "asba", "block", "broker", "brokers", "buyers",
    "cdp", "cfo", "cogs", "collection", "companies", "contracts", "corporate",
    "csr", "ctc", "cum", "day", "department", "deposit", "facilities", "fig",
    "icai", "icdr", "ind", "insurance", "ipo", "isin", "life", "locations",
    "long", "master", "monitoring", "office", "ops", "pension", "qualified",
    "refund", "registered", "regulation", "risks", "rta", "rules", "rupees",
    "scra", "scsb", "short", "size", "term", "total", "unit",
    # Third pass: standards, headings and stock phrases.
    "accounting", "chartered", "closes", "dollars", "engineer", "european",
    "exchange", "foreign", "independent", "mandate", "request", "standard",
    "standards", "time", "union",
    # Stopwords, so a dangling "and" or "the" is trimmed from a span edge.
    "and", "of", "the",
    # Fourth pass, from scored false positives: "FACE VALUE" alone accounted for
    # 13 of 26, and the rest are table headings and label text.
    "address", "banks", "card", "certified", "constitute", "credit", "e",
    "email", "face", "ip", "mail", "on", "self", "shall", "value",
    # Newspaper boilerplate, which the model reads as a person's name.
    "circulated", "daily", "edition", "editions", "english", "hindi",
    "marathi", "national", "newspaper", "regional", "widely",
    # "BID/OFFE R" is a line break inside a heading in the source document.
    "offe",
    # Engineering and unit words. The model reads "Air Conditioning" as a name,
    # and because the gazetteer is case insensitive one such mistake spreads to
    # every lowercase "air conditioning" in the document.
    "air", "amperes", "circuit", "conditioning", "kilometer", "kilometers",
    "kilometre", "kilometres", "mega", "photo", "volt", "voltaic", "volts",
    "watt", "watts",
}

# Public bodies, exchanges and depositories. Referenced by law, not personal
# data: redacting them would make the document unreadable for no privacy gain.
INSTITUTIONS = {
    "sebi", "securities and exchange board of india", "bse", "nse",
    "bombay stock exchange", "national stock exchange", "rbi",
    "reserve bank of india", "roc", "registrar of companies",
    "ministry of corporate affairs", "government of india", "nsdl", "cdsl",
    "income tax department", "central government", "state government",
    "supreme court", "high court", "lok sabha", "parliament",
    "insurance regulatory and development authority", "irdai",
    "competition commission of india", "national company law tribunal",
    "nclt", "fema", "companies act",
}

# Countries and states. A state alone identifies nobody, and blanket-redacting
# "India" 97 times would destroy the document.
GEO_KEEP = {
    "india", "bharat", "republic of india", "united states",
    "united states of america", "us", "u.s.", "usa", "uk", "united kingdom",
    "uae", "sweden", "singapore", "china", "japan", "germany", "france",
    "andhra pradesh", "assam", "bihar", "delhi", "goa", "gujarat", "haryana",
    "karnataka", "kerala", "madhya pradesh", "maharashtra", "odisha",
    "punjab", "rajasthan", "tamil nadu", "telangana", "uttar pradesh",
    "west bengal",
}

# Model noise: units, acronyms and abbreviations it labels as places. Compared
# with full stops removed, so "N.A", "N.A." and "NA" all match one entry.
NOT_A_PLACE = {
    "na", "ay", "mt", "pv", "upi", "bess", "kilovolt", "yojana", "hindi",
    "progress", "allotted", "shareholder", "karta", "n/a", "gst", "pan", "tds",
    "roc", "cin", "isin", "ifsc", "nav", "eps", "ebitda",
}

COMPANY_SUFFIXES = (
    "limited", "ltd", "ltd.", "llp", "inc", "inc.", "corporation", "corp",
    "plc", "bank", "trust", "partners", "associates", "ventures", "holdings",
    "industries", "enterprises", "technologies", "securities", "capital",
    "advisors", "advisory", "consultants", "solutions", "services", "systems",
    "group",
)

# A span built only from these is a fragment such as "Bank Limited" or
# "FAMILY TRUST", not a company that identifies anyone.
GENERIC_ORG = set(COMPANY_SUFFIXES) | {"private", "family", "and", "of", "the", "co"}

# Words that mark a span as a place even when the model calls it a person.
PLACE_WORDS = {
    "apartment", "bhavan", "building", "bungalow", "chambers", "chowk",
    "colony", "complex", "district", "east", "estate", "facility", "farm",
    "farms", "floor",
    "gat", "gymkhana", "hospital", "house", "industrial", "khed", "layout",
    "marg", "nagar", "north", "opp", "park", "phase", "plot", "premises",
    "road", "sector", "showroom", "society", "south", "tal", "taluka",
    "tehsil", "tower", "village", "west", "wing", "centre", "center", "no",
}

_WORD = re.compile(r"\S+")
_SPLIT = re.compile(r"[\s/()\[\]-]+")
_STRIP = ".,;:()[]{}'\"“”‘’*^&-"


def normalise(word: str) -> str:
    return word.strip(_STRIP).lower()


def tokens(text: str):
    return [token for token in _SPLIT.split(text) if token]


def words_of(text: str):
    return [word for word in (normalise(token) for token in tokens(text)) if word]


def all_jargon(text: str) -> bool:
    # Single characters are ignored: they are footnote markers and line-break
    # debris, and they should not stop a heading being recognised as a heading.
    words = [word for word in words_of(text) if len(word) > 1]
    return bool(words) and all(word in JARGON for word in words)


def has_company_suffix(text: str) -> bool:
    words = words_of(text)
    return bool(words) and words[-1] in COMPANY_SUFFIXES


def has_place_word(text: str) -> bool:
    return bool(set(words_of(text)) & PLACE_WORDS)


def all_generic(text: str) -> bool:
    words = words_of(text)
    return bool(words) and all(word in GENERIC_ORG for word in words)


def is_institution(text: str) -> bool:
    """True for public bodies, including the fragments spaCy produces of them."""
    lowered = " ".join(words_of(text))
    if not lowered:
        return False
    return any(
        name in lowered or (len(lowered) >= 3 and lowered in name)
        for name in INSTITUTIONS
    )


def has_digit(text: str) -> bool:
    return any(character.isdigit() for character in text)


def strip_jargon_edges(value: str):
    """Offsets of `value` with leading and trailing jargon words removed.

    "Sharmila Joshi Website" is a real name with a stray label attached, and
    "Rajesh Branch" is a real name with a stray noun. Trimming the edges keeps
    the name and drops the rest; None means nothing but jargon was left.
    """
    found = [(m.start(), m.end(), normalise(m.group())) for m in _WORD.finditer(value)]
    low, high = 0, len(found)
    while low < high and found[low][2] in JARGON:
        low += 1
    while high > low and found[high - 1][2] in JARGON:
        high -= 1
    if low >= high:
        return None
    return found[low][0], found[high - 1][1]
