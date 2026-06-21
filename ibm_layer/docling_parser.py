"""
ibm_layer/docling_parser.py

Downloads the IFAB Laws of the Game 2025/26 PDF, parses Laws 9, 11, 12,
14 with Docling, and writes PARAPHRASED summaries to law_chunks.json.

COPYRIGHT WARNING: this script must never write verbatim IFAB text into
law_chunks.json. Docling extraction gives you exact source text; the
paraphrasing step below is a deliberate, separate transformation step,
not optional cleanup.

SCHEMA WARNING: I don't have your real contracts.py OfficiatingScenario
definition. The law_chunks.json schema below is my best guess based on
what tools.py's get_law_text() needs (law_number, title, summary).
Cross-check against contracts.py and officiating_scenarios.json's
existing 2 seeded scenarios before finalizing field names.

Run this as: python ibm_layer/docling_parser.py
"""

from __future__ import annotations

import json
from pathlib import Path

try:
    from docling.document_converter import DocumentConverter
except ImportError as e:
    raise ImportError(
        "Could not import DocumentConverter from docling.document_converter. "
        "This matches docling's documented API as of recent 2.x releases, "
        "but if docling==2.103.0 has moved this, run "
        "`python -c \"import docling; help(docling)\"` locally and fix this "
        "import path."
    ) from e

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / "data" / "docs"
PDF_PATH = DOCS_DIR / "IFAB-Laws-of-the-Game-2025_26.pdf"
PDF_URL = "https://assets.the-afc.com/downloads/referees/IFAB-Laws-of-the-Game-2025_26.pdf"

LAW_CHUNKS_OUTPUT = Path(__file__).resolve().parent / "law_chunks.json"

# The four laws in scope per the project brief. Titles are taken from the
# publicly known IFAB Laws of the Game numbering and should be
# cross-checked against the actual downloaded PDF's table of contents,
# since IFAB occasionally renumbers or retitles laws between editions.
LAWS_TO_PARSE = {
    9: "The Ball",
    11: "Offside",
    12: "Fouls and Misconduct",
    14: "The Penalty Kick",
}


def download_pdf() -> Path:
    """Download the Laws of the Game PDF if not already present locally."""
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    if PDF_PATH.exists():
        print(f"PDF already present at {PDF_PATH}, skipping download.")
        return PDF_PATH

    import urllib.request

    print(f"Downloading {PDF_URL} ...")
    try:
        req = urllib.request.Request(
            PDF_URL,
            headers={"User-Agent": "Mozilla/5.0 (compatible; FineMarginsBot/1.0)"},
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
        PDF_PATH.write_bytes(data)
        print(f"Saved to {PDF_PATH} ({len(data) / 1024:.0f} KB)")
    except Exception as e:
        raise RuntimeError(
            f"Failed to download PDF from {PDF_URL}. This may be a network "
            f"issue, a changed URL (the-afc.com restructures asset paths "
            f"periodically), or a User-Agent block. If this URL is dead, "
            f"search 'IFAB Laws of the Game 2025/26 PDF' for IFAB's own "
            f"hosted copy at theifab.com as a fallback source. "
            f"Original error: {e}"
        ) from e

    return PDF_PATH


def extract_full_text(pdf_path: Path) -> str:
    """Run Docling's DocumentConverter over the PDF and return plain text
    (markdown export) of the whole document. Law-specific slicing happens
    in a separate step since Docling doesn't know IFAB's law numbering."""
    converter = DocumentConverter()
    result = converter.convert(str(pdf_path))
    # export_to_markdown() is Docling's documented text-extraction API;
    # confirm this method name still exists in your installed version —
    # if it errors, check result.document's available export_to_* methods.
    return result.document.export_to_markdown()


def slice_law_sections(full_text: str) -> dict[int, str]:
    """
    Naive section slicer: finds each "Law N" heading in the extracted
    markdown and grabs the text up to the next "Law N+1" heading.

    This is a starting heuristic, not guaranteed robust — Docling's
    markdown output structure depends on how well it parses the PDF's
    actual layout (multi-column rules documents can confuse text
    extraction order). After running this once, manually inspect the
    sliced sections against the real PDF before trusting them, especially
    for Law 11 (Offside) and Law 12 (Fouls and Misconduct), which are
    long and have many subsections.
    """
    import re

    sections: dict[int, str] = {}
    law_numbers = sorted(LAWS_TO_PARSE.keys())

    for law_num in law_numbers:
        pattern = rf"(?:^|\n)#{{1,3}}\s*Law\s+{law_num}\b"
        match = re.search(pattern, full_text, re.IGNORECASE)
        if not match:
            print(
                f"WARNING: could not find a 'Law {law_num}' heading in the "
                f"extracted text. Docling's markdown structure may differ "
                f"from this regex's assumptions — inspect full_text "
                f"manually (e.g. dump it to a .md file) and adjust the "
                f"pattern in slice_law_sections()."
            )
            continue

        start = match.start()
        next_law_candidates = [
            re.search(rf"(?:^|\n)#{{1,3}}\s*Law\s+{n}\b", full_text[start + 10:], re.IGNORECASE)
            for n in range(law_num + 1, 18)
        ]
        next_matches = [m for m in next_law_candidates if m]
        if next_matches:
            end = start + 10 + min(m.start() for m in next_matches)
        else:
            end = len(full_text)

        sections[law_num] = full_text[start:end].strip()

    return sections


def paraphrase_section(law_num: int, title: str, raw_text: str) -> str:
    """
    Produce a PARAPHRASED summary of a law section — never verbatim.

    PLACEHOLDER IMPLEMENTATION: this currently does basic bookkeeping,
    which is NOT the same as paraphrasing and is NOT safe to ship as-is.
    You have two real options once you run this:

    Option A (manual, fastest for 4 laws): print raw_text for each law,
    read it, and hand-write a 3-5 sentence paraphrase per law into
    law_chunks.json directly. For exactly 4 laws this is the most
    reliable path before a deadline.

    Option B (automated via Granite once live): once granite_client.py
    is confirmed working against your real watsonx.ai account, replace
    this function's body with a call like:

        from ibm_layer.granite_client import get_granite_response  # adjust
        prompt = (
            f"Paraphrase the following football law text in your own "
            f"words, in 3-5 sentences, preserving all rule meaning but "
            f"using no more than 3 consecutive words matching the "
            f"original phrasing at a time. Do not quote directly.\n\n"
            f"{raw_text[:3000]}"
        )
        return get_granite_response(prompt)

    This function currently returns a flagged stub so nothing gets
    silently written to law_chunks.json that isn't actually safe to
    display.
    """
    return (
        f"[UNPARAPHRASED PLACEHOLDER -- DO NOT SHIP] "
        f"Raw extracted text for Law {law_num} ({title}) is "
        f"{len(raw_text)} characters. Replace this with a real paraphrase "
        f"via Option A or B described in paraphrase_section()'s docstring "
        f"before this goes into the demo."
    )


def build_law_chunks() -> list[dict]:
    pdf_path = download_pdf()
    full_text = extract_full_text(pdf_path)

    raw_dump_path = DOCS_DIR / "extracted_full_text.md"
    raw_dump_path.write_text(full_text, encoding="utf-8")
    print(f"Full extracted text dumped to {raw_dump_path} for manual review.")

    sections = slice_law_sections(full_text)

    chunks = []
    for law_num, title in LAWS_TO_PARSE.items():
        raw_text = sections.get(law_num, "")
        if not raw_text:
            print(f"Skipping Law {law_num} -- no text extracted, see warning above.")
            continue
        chunks.append(
            {
                "law_number": law_num,
                "title": title,
                "summary": paraphrase_section(law_num, title, raw_text),
                "source": "IFAB Laws of the Game 2025/26",
                "source_url": PDF_URL,
            }
        )

    return chunks


def main():
    chunks = build_law_chunks()

    if not chunks:
        print(
            "No law chunks were produced. Check the warnings above -- most "
            "likely the heading regex in slice_law_sections() doesn't "
            "match this PDF's actual structure. Inspect "
            "data/docs/extracted_full_text.md directly."
        )
        return

    LAW_CHUNKS_OUTPUT.write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nWrote {len(chunks)} law chunk(s) to {LAW_CHUNKS_OUTPUT}")
    print(
        "\nREMINDER: summaries are currently PLACEHOLDER stubs, not "
        "real paraphrases. See paraphrase_section()'s docstring for the "
        "two ways to finish this before the demo."
    )


if __name__ == "__main__":
    main()