import pytest
from unittest.mock import MagicMock, patch
import os, tempfile
from scripts.pdf_resolver import download_pdf, is_valid_pdf


def test_is_valid_pdf_accepts_real_pdf():
    content = b"%PDF-1.4 fake content"
    assert is_valid_pdf(content) is True


def test_is_valid_pdf_rejects_html():
    content = b"<!DOCTYPE html><html><body>Login required</body></html>"
    assert is_valid_pdf(content) is False


def test_is_valid_pdf_rejects_empty():
    assert is_valid_pdf(b"") is False


def test_download_pdf_raises_on_html_content():
    """download_pdf must raise ValueError when server returns HTML instead of PDF."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status = MagicMock()
    mock_response.headers = {"content-type": "text/html"}

    html_chunks = [b"<!DOCTYPE html>", b"<html>Paywall</html>"]
    mock_response.iter_bytes = MagicMock(return_value=iter(html_chunks))
    mock_client.stream.return_value = mock_response

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        tmp_path = f.name
    try:
        with pytest.raises(ValueError, match="not a valid PDF"):
            download_pdf(mock_client, "https://example.com/paper.pdf", tmp_path)
        # File must not be left behind on failure
        assert not os.path.exists(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_download_pdf_succeeds_on_real_pdf():
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.raise_for_status = MagicMock()
    mock_response.headers = {"content-type": "application/pdf"}

    # Real PDF magic bytes + some content
    pdf_chunks = [b"%PDF-1.4 ", b"fake-pdf-content"]
    mock_response.iter_bytes = MagicMock(return_value=iter(pdf_chunks))
    mock_client.stream.return_value = mock_response

    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "test.pdf")
        download_pdf(mock_client, "https://example.com/paper.pdf", out_path)
        assert os.path.exists(out_path)
        with open(out_path, "rb") as f:
            assert f.read().startswith(b"%PDF")
