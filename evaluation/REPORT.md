# Evaluation Report

## What was measured

Detections were scored against ground truth written by hand, by reading the
document's text directly. Annotating from the tool's own output would have
produced a test that could only ever report success, so the annotations were
written first and the tool was run against them afterwards.

Two annotation sets, 99 spans in total.

| set | source | scope | blocks read | blocks with PII | spans |
|---|---|---|---|---|---|
| `ground_truth.json` | Red Herring Prospectus | blocks 1–134 | 128 | 35 | 88 |
| `ground_truth_synthetic.json` | `test_synthetic.docx` | whole file | 9 | 9 | 11 |

**Why a sample.** The prospectus is 4,201 blocks. Annotating all of them by hand
was not realistic, so the cover pages and front matter were annotated in full.
That region carries almost all of the document's contact detail: both offices,
the company secretary, both book running lead managers with their contact
people, the registrar and the full promoter list. A dense, fully-read region
gives a meaningful denominator; a scattered sample would not.

**Why a synthetic file as well.** The prospectus contains no SSN, credit card,
IP address or date of birth, which is expected of an Indian SEBI filing. Without
a second set, four of the nine required PII types would have no measurement at
all. Its values are fabricated, so its ground truth is exact rather than a
judgement.

**Blocks with no PII are part of the sample.** 93 of the 128 prospectus blocks
read contain nothing. They were read and found clean, and a detection in one of
them counts against precision. Without recording the range read, there is no
denominator and precision cannot be computed honestly.

## How a detection is counted

Annotation granularity and detection granularity do not have to agree. The
ground truth lists `Chakan` and `Khed` as two places; the tool may emit
`Chakan Taluka - Khed` as one span. Both places left the document, and one-to-one
matching would call that one hit and one miss.

So coverage is measured in each direction separately:

- **recall** — was each annotated span overlapped by some detection?
- **precision** — did each detection overlap some annotation?

The two hit counts differ and both are printed rather than collapsed into a
single figure. Scoring with one-to-one pairing instead is available via
`--strict-pairing`; on the final tool it gives typed F1 0.936 against 0.942, so
the choice is worth 0.006 and is reported for transparency rather than because
it flatters the result.

Every run is scored twice:

- **typed** — the tool must also agree which kind of PII the span is.
- **redacted at all** — only asks whether the span left the document.

They differ because spaCy moves names between `PERSON` and `ORG` freely, and a
person's name replaced by a company name has still been redacted.

**Accuracy** is reported as `(covered + matched) / (annotated + detected)`. There
is no meaningful count of true negatives when the task is finding spans in free
text, so the textbook formula does not apply; this is the share of all spans, on
both sides, that were accounted for. The definition is stated rather than left
for the reader to infer.

## Results

### Prospectus sample

| type | covered | missed | matched | spurious | precision | recall | F1 |
|---|---|---|---|---|---|---|---|
| EMAIL | 5 | 0 | 5 | 0 | 1.000 | 1.000 | 1.000 |
| PHONE | 5 | 0 | 5 | 0 | 1.000 | 1.000 | 1.000 |
| PERSON | 23 | 2 | 22 | 0 | 1.000 | 0.920 | 0.958 |
| ORGANIZATION | 26 | 2 | 26 | 2 | 0.929 | 0.929 | 0.929 |
| LOCATION | 23 | 2 | 23 | 2 | 0.920 | 0.920 | 0.920 |
| **typed total** | **82** | **6** | **81** | **4** | **0.953** | **0.932** | **0.942** |
| **redacted at all** | **84** | **4** | **83** | **2** | **0.976** | **0.955** | **0.965** |

Accuracy: **0.942** typed, **0.965** untyped.

### Synthetic file

| type | precision | recall | F1 |
|---|---|---|---|
| SSN | 1.000 | 1.000 | 1.000 |
| CREDIT_CARD | 1.000 | 1.000 | 1.000 |
| IP_ADDRESS | 1.000 | 1.000 | 1.000 |
| DATE_OF_BIRTH | 1.000 | 1.000 | 1.000 |
| EMAIL / PHONE / PERSON / ORGANIZATION | 1.000 | 1.000 | 1.000 |
| LOCATION | 1.000 | 0.667 | 0.800 |
| **typed total** | **1.000** | **0.909** | **0.952** |

Accuracy: **0.952**. The single miss is `MG Road`, which the model does not tag
and no pattern covers.

### Effect of the linking pass

| | precision | recall | F1 |
|---|---|---|---|
| two passes | 0.953 | 0.932 | 0.942 |
| `--single-pass` | 0.975 | 0.886 | 0.928 |

The first pass costs a little precision and buys more recall. It also fixes two
things the scores do not capture: it stops two different promoters being merged
into one fake identity, and it closes partial-name leaks such as
`ROHIT KUSHAL HEGDE` coming out as a live `ROHIT` beside a redacted surname.

## Every remaining error

Ten on the prospectus sample, one on the synthetic file. All are in
`results.json`.

| block | type | value | what happened |
|---|---|---|---|
| 22, 122 | PERSON | `RAKHI GIRIJA SHETTY` | detected and redacted, but labelled an organisation |
| 22, 122 | ORGANIZATION | `RAKHI GIRIJA SHETTY` | the other half of the same confusion |
| 17, 119 | LOCATION | `Tower 2` | an address component I did not annotate |
| 17, 119 | LOCATION | `Pallod Farms` | the model does not tag it; no pattern covers it |
| 126 | ORGANIZATION | `JANSATTA`, `LOKSATTA` | single-token organisations, dropped by design |
| synthetic 5 | LOCATION | `MG Road` | the model does not tag it |

**Four of the ten are one confusion.** `RAKHI GIRIJA SHETTY` is redacted every
time it appears; it is filed as an organisation, which costs a miss and a false
positive at once. This is the clearest argument for reporting the untyped row: it
is a labelling error, not a leak.

**Two are my annotation, not the tool.** `Tower 2` is part of the mailing
address and should have been annotated. The ground truth was deliberately left
unchanged rather than edited after seeing results, so reported precision is
slightly worse than reality rather than better.

## Errors beyond the scored sample

Found by reading the full redacted output, and not reflected in the numbers
above because they fall outside the annotated range.

- **Names written with an internal tab**, such as `Sunil\tNagayya Shetty`, are
  missed when that is their only occurrence in the document.
- **Type confusion can leave a fragment.** `Narayna B. Shetty` came out as
  `Reyestown B. Shetty`, the first name having been replaced as a place.
- **The issuer's website survives.** URLs are out of scope, though
  `www.kshinternational.com` does identify the company.

## How the numbers moved

Successive scored runs, each after acting on the previous run's error list.

| run | typed precision | recall | F1 |
|---|---|---|---|
| baseline, before any tuning | 0.690 | 0.659 | 0.674 |
| coverage matching and first vocabulary batch | 0.867 | 0.773 | 0.817 |
| city, postal code and paired-name recognizers | 0.919 | 0.909 | 0.914 |
| company-by-suffix recognizer, more vocabulary | 0.942 | 0.932 | 0.937 |
| final, after rejecting the `India Limited` fragment | 0.953 | 0.932 | 0.942 |

An honest note on the second row: the matching rule and the first vocabulary
batch were changed together, so their contributions cannot be separated after the
fact. Measured on the finished tool, the matching rule is worth 0.006, because
the recognizers now emit finer spans and the granularity mismatch that motivated
the change has largely gone.

Some of what these runs fixed was the harness rather than the tool. The first
run reported LOCATION recall of 0.200; most of those were not misses but the
pairing artefact described above, and the postal code pattern was refusing a
trailing comma, which is exactly how an address continues.

## Threats to validity

- **One annotator, no adjudication.** The conventions are written down in the
  ground truth files, but nobody checked them independently.
- **The sample is dense, not representative.** The front matter is where the
  contact detail lives. Precision measured over the whole document, most of which
  is prose about risk factors and regulation, would probably be lower.
- **The tool was tuned against this sample**, so these numbers are optimistic in
  the way any held-in test set is. A second annotated region, kept unseen until
  the end, would have been better and was not affordable in the time.
- **The synthetic file is easy.** Nine labelled lines, one value each. It shows
  the four unrepresented types work at all, not that they work in prose.

## Reproducing

```bash
.venv\Scripts\python.exe evaluation\ground_truth.py       # validate annotations
.venv\Scripts\python.exe evaluation\score.py              # the tables above
.venv\Scripts\python.exe evaluation\score.py --single-pass
.venv\Scripts\python.exe evaluation\score.py --strict-pairing
```

`--json results.json` writes the raw counts, including every miss and false
positive.
