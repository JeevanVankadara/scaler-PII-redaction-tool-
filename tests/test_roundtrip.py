"""Proves the read/write path is lossless before any redaction logic exists.

Run with: python tests/test_roundtrip.py <source.docx>
"""

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pii_redactor.docx_io import iter_blocks, load
from pii_redactor.pipeline import run
from pii_redactor.transforms import passthrough

MEDIA_AND_STYLES = ("word/media/", "word/styles.xml", "word/numbering.xml")


def document_text(path):
    return "\n".join(b.text for b in iter_blocks(load(path)))


def counts(path):
    document = load(path)
    return {
        "tables": len(document.tables),
        "paragraphs": len(document.paragraphs),
        "sections": len(document.sections),
    }


def preserved_parts(path):
    with zipfile.ZipFile(path) as archive:
        return {
            name
            for name in archive.namelist()
            if name.startswith(MEDIA_AND_STYLES)
        }


def main(source):
    source = Path(source)
    with tempfile.TemporaryDirectory() as tmp:
        destination = Path(tmp) / "roundtrip.docx"
        stats = run(source, destination, passthrough)

        before, after = document_text(source), document_text(destination)
        assert before == after, "text changed during a passthrough run"
        assert counts(source) == counts(destination), "structure changed"

        missing = preserved_parts(source) - preserved_parts(destination)
        assert not missing, f"lost parts: {sorted(missing)}"

    print(f"ok  text identical ({len(before):,} chars)")
    print(f"ok  structure identical ({counts(source)})")
    print(f"ok  media and styles preserved")
    print(f"\n{stats.blocks} blocks in {stats.seconds:.1f}s")


if __name__ == "__main__":
    default = Path(__file__).resolve().parent.parent / "files" / "Red Herring Prospectus.docx"
    main(sys.argv[1] if len(sys.argv) > 1 else default)
