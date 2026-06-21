"""
ibm_layer/docling_parser.py

VERIFIED: docling==2.103.0 installs cleanly, DocumentConverter.convert()
takes a path/URL/str and returns a ConversionResult with .document.export_to_markdown().

VERIFIED SOURCE: https://assets.the-afc.com/downloads/referees/IFAB-Laws-of-the-Game-2025_26.pdf
is real, public, and cleanly text-extractable. Confirmed table of contents
with exact page numbers per Law:
  Law 9  The Ball In and Out of Play .......... p.95
  Law 11 Offside ............................... p.51
  Law 12 Fouls and Misconduct .................. p.55
  Law 14 The Penalty Kick ...................... p.79
  Video Assistant Referee (VAR) protocol ....... p.146

COPYRIGHT NOTE: the PDF itself says it "may not be reproduced or
translated in whole or in part... without permission." Chunk it for
retrieval, but every excerpt surfaced to a user or to Granite must be a
short paraphrase, not the verbatim source text. Don't pipe raw Docling
output straight into the UI or into officiating_scenarios.json — always
pass it through a paraphrase step first.
"""

from pathlib import Path
from docling.document_converter import DocumentConverter

LAW_PAGE_RANGES = {
    9: (95, 102),
    11: (51, 54),
    12: (55, 62),
    14: (79, 86),
    "var_protocol": (146, 155),
}


def parse_laws_pdf(pdf_path: str) -> str:
    """pdf_path can be a local file or, per the verified signature, a URL.
    Ashish should download the PDF once (data/docs/laws_of_the_game_2025_26.pdf,
    gitignored — don't commit the copyrighted source file to the repo) rather
    than re-fetching it on every run."""
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    return result.document.export_to_markdown()


def chunk_by_law(full_markdown: str, page_range: tuple[int, int]) -> str:
    """Placeholder — Docling's markdown export doesn't preserve page
    numbers 1:1 by default. Helper Chat 2: either use
    convert(..., page_range=range) to convert just the relevant pages
    per Law directly (cheaper, avoids re-chunking full-doc markdown),
    or post-process page breaks if export includes them. Test both,
    pick whichever gives cleaner chunk boundaries."""
    raise NotImplementedError("Fill in during build — see docstring for the two options to try.")


if __name__ == "__main__":
    # PREFLIGHT CHECK — confirms Docling can actually parse the real target PDF.
    # Run this before building anything else in this file.
    pdf = "data/docs/laws_of_the_game_2025_26.pdf"
    if not Path(pdf).exists():
        print(f"Download the PDF first: curl -o {pdf} "
              f"https://assets.the-afc.com/downloads/referees/IFAB-Laws-of-the-Game-2025_26.pdf")
    else:
        md = parse_laws_pdf(pdf)
        print(f"Parsed {len(md)} characters of markdown.")
        print(md[:500])
