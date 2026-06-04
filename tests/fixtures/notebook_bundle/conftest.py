"""Pytest-Fixtures für notebook-bundle Tests."""
import io
import json
import pytest
from pypdf import PdfWriter


def make_mock_pdf(title: str, num_pages: int = 3) -> bytes:
    """Erzeugt ein minimales PDF mit num_pages leeren Seiten."""
    writer = PdfWriter()
    for i in range(num_pages):
        writer.add_blank_page(width=595, height=842)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.fixture(scope="session")
def fixture_dir(tmp_path_factory):
    """Temporäres Verzeichnis mit 5 Mock-PDFs und selection.json."""
    d = tmp_path_factory.mktemp("notebook_bundle")
    paper_ids = ["smith2020", "jones2019", "brown2021", "zhang2022", "lee2023"]
    titles = [
        "Deep Learning for NLP",
        "Transformer Architectures",
        "Few-Shot Learning in LLMs",
        "Instruction Tuning Approaches",
        "RLHF and Alignment",
    ]
    authors_list = [
        ["Smith, J.", "Doe, A."],
        ["Jones, B."],
        ["Brown, C.", "White, D."],
        ["Zhang, L."],
        ["Lee, K.", "Park, M."],
    ]
    years = [2020, 2019, 2021, 2022, 2023]

    papers = []
    for pid, title, authors, year in zip(paper_ids, titles, authors_list, years):
        pdf_path = d / f"paper_{pid}.pdf"
        pdf_path.write_bytes(make_mock_pdf(title, num_pages=3))
        papers.append(
            {
                "id": pid,
                "title": title,
                "authors": authors,
                "year": year,
                "pdf_path": str(pdf_path),
            }
        )

    selection_path = d / "selection.json"
    selection_path.write_text(json.dumps({"papers": papers}, indent=2))
    return d
