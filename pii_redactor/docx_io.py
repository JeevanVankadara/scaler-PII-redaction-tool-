"""Reading a .docx into TextBlocks and writing it back out."""

from docx import Document as open_document
from docx.document import Document as DocxDocument
from docx.oxml.ns import qn
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from .blocks import TextBlock


def load(path):
    return open_document(str(path))


def save(document, path) -> None:
    document.save(str(path))


def iter_blocks(document, include_headers: bool = True):
    """Yield every paragraph in the document, including inside tables and headers.

    Merged table cells and linked headers surface the same underlying XML more
    than once, so each paragraph element is yielded at most once.
    """
    seen = set()
    yield from _walk(document, "body", seen)
    if include_headers:
        yield from _walk_headers(document, seen)


def _walk(container, location: str, seen: set):
    for item in _iter_block_items(container):
        if isinstance(item, Paragraph):
            # Hold the element itself: lxml reuses proxies, but only while referenced.
            if item._p in seen:
                continue
            seen.add(item._p)
            block = _to_block(item, location)
            if block is not None:
                yield block
        else:
            yield from _walk_table(item, location, seen)


def _walk_table(table: Table, location: str, seen: set):
    for row_index, row in enumerate(table.rows):
        for cell_index, cell in enumerate(row.cells):
            yield from _walk(cell, f"{location}/table[{row_index},{cell_index}]", seen)


def _walk_headers(document, seen: set):
    for index, section in enumerate(document.sections):
        parts = (
            ("header", section.header),
            ("first_page_header", section.first_page_header),
            ("even_page_header", section.even_page_header),
            ("footer", section.footer),
            ("first_page_footer", section.first_page_footer),
            ("even_page_footer", section.even_page_footer),
        )
        for name, part in parts:
            if part is not None:
                yield from _walk(part, f"section[{index}]/{name}", seen)


def _to_block(paragraph: Paragraph, location: str):
    runs = _ordered_runs(paragraph)
    if not runs:
        return None
    return TextBlock(runs, location)


def _ordered_runs(paragraph: Paragraph):
    """Runs in visual order, including those nested inside hyperlinks."""
    runs = []
    for child in paragraph._p.iterchildren():
        if child.tag == qn("w:r"):
            runs.append(Run(child, paragraph))
        elif child.tag == qn("w:hyperlink"):
            runs.extend(Run(run, paragraph) for run in child.findall(qn("w:r")))
    return runs


def _iter_block_items(parent):
    if isinstance(parent, DocxDocument):
        element = parent.element.body
    elif isinstance(parent, _Cell):
        element = parent._tc
    else:
        element = parent._element

    for child in element.iterchildren():
        if child.tag == qn("w:p"):
            yield Paragraph(child, parent)
        elif child.tag == qn("w:tbl"):
            yield Table(child, parent)
