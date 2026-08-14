# PII Redaction Tool

Reads a `.docx`, replaces the personally identifiable information in it with
plausible fake values, and writes a new `.docx` that still looks like the
original document.

Built against a Red Herring Prospectus — a draft IPO document filed with SEBI —
which is 4,201 paragraphs, 76 tables, 85 sections and 12 MB of XML.

```
Rashi Patil            ->  John Doe
rashi.patil@gmail.com  ->  john.doe@example.com
+91 9876543210         ->  +91 1234567645
```

## Running it

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

```bash
.venv\Scripts\python.exe -m pii_redactor.cli "files\Red Herring Prospectus.docx" -o out.docx
```

Useful flags: `--mapping FILE` writes the real-to-fake mapping as JSON for
review, `-p placeholder` swaps fake values for `[EMAIL]` style markers,
`--only email,phone` restricts which recognizers run, and `--single-pass` skips
the linking pass for speed. `--help` lists the rest.

A full run over the prospectus takes about 55 seconds and makes 933
replacements: 394 organisations, 273 places, 178 people, 52 emails, 36 phone
numbers.

## Web interface

A Flask REST API and a React front end. Upload a `.docx`, watch it process, read
the counts by category, browse every value that was detected beside what replaced
it, download the result.

```bash
cd web && npm install && npm run build
```

```bash
.venv\Scripts\python.exe -m server.app
```

Then open `http://localhost:8000`. For front-end work run `npm run dev` in `web/`
alongside the server; Vite proxies `/api` to it, so there is no CORS
configuration anywhere.

| method | route | |
|---|---|---|
| `GET` | `/api/health` | liveness, used by the Render health check |
| `POST` | `/api/jobs` | upload a `.docx`, returns a job id |
| `GET` | `/api/jobs/{id}` | status and, once finished, the counts |
| `GET` | `/api/jobs/{id}/mapping` | every detected value and its replacement |
| `GET` | `/api/jobs/{id}/download` | the redacted `.docx` |
| `DELETE` | `/api/jobs/{id}` | drop the job and its files |

A full run takes about a minute, which is too long for one request to hold open,
so uploads start a background job and the page polls it.

**The mapping endpoint returns unredacted source data.** It is the one thing that
can reverse the pseudonymization. It is served `no-store`, never logged, and the
table carries a warning. Do not expose this server to a network you do not
control.

## Deploying to Render

One web service serves both halves. The `Dockerfile` builds the React bundle in a
Node stage and copies it into the Python stage, so there is a single URL, no CORS
and no second deployment to keep in sync.

1. New → Web Service → connect this repository.
2. Runtime **Docker**; Render reads the `Dockerfile` and needs no build command.
3. Health check path `/api/health`.

`render.yaml` describes the same thing as a blueprint if you would rather deploy
that way.

**Memory is the thing to watch.** The free instance has 512 MB. spaCy plus a
document the size of the prospectus parsed into an XML tree can exceed that, and
the process is killed mid-run. The blueprint asks for `starter` for that reason;
the free plan is fine for the small test files. Free instances also sleep after
inactivity, so the first upload after a pause waits for a cold start.

## Approach

**Hybrid: patterns for structured PII, a model for the rest.** Emails, phone
numbers, SSNs, credit cards, IP addresses, dates of birth, postal codes and
company names ending in a legal suffix all have a shape, and a pattern beats a
model on them every time. Names, organisations and places have no shape, so
those come from spaCy's `en_core_web_sm`.

**The document is edited in place, not rebuilt.** A paragraph's text is split
across runs at arbitrary points, so a name can span three of them. `TextBlock`
flattens the runs into one string, lets a recognizer work on plain character
offsets, then maps the edit back — new text into the first run touched, tails
preserved on the rest. Rebuilding the document from extracted text would have
destroyed 76 tables, the styling, the headers and the images. A round-trip test
asserts that a no-op run leaves text, structure and media identical.

**Most of the work is filtering, not detection.** Raw spaCy on this document
labels `Offer` a person 113 times and `Equity Shares` an organisation 37 times.
The recognizers in `recognizers/ner.py` sit on top of it with a document
vocabulary, an institution list, edge trimming and case rules. That filtering is
what makes the model's output safe to act on.

**Two passes.** The first pass collects every name and company in the document.
That matters twice: it decides whether a short name like "Kushal Hegde" is an
unambiguous short form or sits inside several full names, and it builds a
gazetteer so a name found in one paragraph is also found in the paragraph where
the model only caught half of it. Worth 0.928 to 0.942 in typed F1.

**Identities, not substitutions.** A person and their email address resolve to
one identity, so a name and the address derived from it stay consistent with
each other. Everything else keeps the shape of what it replaced: phone numbers
keep their punctuation and country code, dates keep their format, generated
cards pass Luhn, and an all-caps name is replaced by an all-caps name. Values
are seeded from the original text, so runs are reproducible.

## Adding a PII type

One class and one import. Nothing in the engine, pipeline or docx layer changes,
and there is a test asserting exactly that.

```python
@register
class PanRecognizer(RegexRecognizer):
    name, label, priority = "pan", "PAN", 85
    pattern = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b")
```

`RegexRecognizer` gives two hooks: `validate(match)` to reject false positives a
pattern cannot (the Luhn check on cards uses it) and `score_of(match)` when
confidence varies. `ContextualRegexRecognizer` adds a required cue word nearby.
When two recognizers claim overlapping spans the engine settles it by priority,
then score, then match length, so a validated card beats a phone pattern that
grabbed the same digits.

## Decisions that could reasonably have gone the other way

**Company names are redacted, but regulators are not.** SEBI, the stock
exchanges, the depositories and the Registrar of Companies are named because the
law requires it, not because they identify anyone, and redacting them makes the
document unreadable for no privacy gain. Matched by substring, since spaCy
produces fragments of them.

**Countries and states are not redacted; cities and localities are.** "India"
appears 97 times and identifies nobody. "Pune – 410 501" is part of somebody's
mailing address.

**Dates of birth are context gated.** The prospectus contains 276 dates and not
one is a birth date. A date only counts when a birth cue precedes it within 50
characters. This trades recall for precision deliberately: a birth date stated
with no nearby cue is missed, but redacting every date would destroy the
document.

**Single-token organisations are dropped.** Allowing them readmitted `ASBA`,
`IPO`, `Forms`, `Bonus` and `Fraud` for the sake of about seven real names. Cost:
`JANSATTA` and `LOKSATTA`, two single-word newspapers, are missed.

**Not treated as PII:** Corporate Identity Numbers, page references, monetary
amounts, share counts, and filing or agreement dates.

**Out of scope:** URLs. They are not in the assignment's list, though
`www.kshinternational.com` does identify the issuer. Recorded rather than
quietly ignored.

## Results

Measured against hand-written ground truth. Full method and error analysis in
[evaluation/REPORT.md](evaluation/REPORT.md).

| | precision | recall | F1 |
|---|---|---|---|
| Prospectus sample, typed | 0.953 | 0.932 | 0.942 |
| Prospectus sample, redacted at all | 0.976 | 0.955 | 0.965 |
| Synthetic file, typed | 1.000 | 0.909 | 0.952 |

Emails and phone numbers are perfect on the sample. SSNs, credit cards, IP
addresses and dates of birth are perfect on the synthetic file, which exists
because the prospectus contains none of them — expected of an Indian filing.

## Known false positives and negatives

Ten errors remain on the sample, listed in full in `evaluation/results.json`.

- **Four of them are one confusion.** `RAKHI GIRIJA SHETTY` is detected and
  redacted every time, but labelled an organisation rather than a person, which
  costs a miss and a false positive at once. This is why the report carries an
  untyped row: it is a labelling error, not a leak.
- **`Tower 2`, twice.** An address component I failed to annotate, so precision
  is marginally better than the table says. The ground truth was left untouched
  rather than edited after seeing results.
- **`Pallod Farms`, twice.** The model does not tag it and no pattern covers it.
- **`JANSATTA`, `LOKSATTA`.** The single-token organisation trade, above.

Two government scheme names, `Gram Jyoti` and `Kisan Urja Suraksha`, are still
read as people. They could be silenced by adding those words to the vocabulary,
and deliberately are not: Jyoti is a common given name, and the others are
plausible parts of one. Blocking them to tidy up a cosmetic false positive would
cause a real name to leak, which is the wrong trade for a redaction tool.

**The gazetteer multiplies whatever it is given.** It is built from the first
pass and matches case insensitively, so a single bad detection is then applied to
every casing of that phrase in the document — `Air Conditioning` becoming a name
once meant every lowercase `air conditioning` was redacted too. That is why false
positives are fixed at the vocabulary rather than by filtering the gazetteer.

Beyond the scored sample, three leaks are known in the full document. Names
written with a tab inside them, such as `Sunil\tNagayya Shetty`, are missed when
that is their only occurrence. Type confusion can leave a fragment behind, as in
`Reyestown B. Shetty`, where a first name was replaced as a place. And the
issuer's website survives, since URLs are out of scope.

## Layout

```
pii_redactor/
  blocks.py        TextBlock, Replacement, and the run-span mapping
  docx_io.py       reading a .docx into blocks and writing it back
  engine.py        runs recognizers, settles overlaps, emits replacements
  pipeline.py      run() and scan()
  identities.py    one fake identity per real person, and the linking
  surrogates.py    shape-preserving fake values
  policies.py      what a detected value is replaced with
  recognizers/     one module per PII type, plus the registry
evaluation/
  ground_truth*.json   hand-written annotations
  ground_truth.py      loader and validator
  score.py             the scoring harness
  REPORT.md            evaluation report
tests/                 75 unit tests plus a round-trip check
```

## Tests

```bash
.venv\Scripts\python.exe tests\test_engine.py
```

Every file under `tests/` runs standalone with no test runner. `test_roundtrip.py`
checks losslessness against the real prospectus and
`evaluation/ground_truth.py` re-validates every annotation against the live
document.
