"""Contextual Embedding Generation fuer academic_vault (#109).

Generiert 1-Satz-Kontext pro Chunk via Anthropic API mit Prompt-Caching.
Baut embedding_text = context_sentence + chunk_text fuer bessere Retrieval-Qualitaet.
"""
import os
from typing import Optional

def _get_anthropic_client(api_key: Optional[str] = None):
    """Erstellt einen Anthropic-Client.

    Kein Singleton — api_key kann pro Aufruf uebergeben werden.
    Nutzt ANTHROPIC_API_KEY env als Fallback.
    """
    try:
        import anthropic
        key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        return anthropic.Anthropic(api_key=key)
    except ImportError:
        raise ImportError("anthropic SDK nicht installiert. Bitte 'pip install anthropic' ausfuehren.")


def generate_context_sentence(
    chunk_text: str,
    paper_title: str,
    paper_abstract: str,
    paper_id: str,
    api_key: Optional[str] = None,
) -> str:
    """Generiert 1-Satz-Kontext fuer einen Chunk via Anthropic API.

    Nutzt Anthropic Prompt-Caching (cache_control="ephemeral") fuer 50-90%
    Cost-Saving bei wiederholtem Aufruf mit gleichem Paper-Kontext.

    Args:
        chunk_text: Text des Chunks aus dem Paper.
        paper_title: Titel des Papers.
        paper_abstract: Abstract des Papers.
        paper_id: ID des Papers im Vault.
        api_key: Optionaler Anthropic API-Key (Fallback: ANTHROPIC_API_KEY env).

    Returns:
        1-Satz-Kontext, z.B. "Dieser Chunk diskutiert X im Kontext von Y aus Paper Z."
        Bei Fehler: leerer String (graceful degradation).
    """
    try:
        client = _get_anthropic_client(api_key=api_key)

        # System-Prompt mit cache_control fuer Prompt-Caching
        system_prompt = (
            "Du bist ein akademischer Assistent. Deine Aufgabe: Schreibe einen praezisen "
            "1-Satz-Kontext fuer einen Textabschnitt aus einem wissenschaftlichen Paper. "
            "Der Kontext soll das Retrieval verbessern, indem er beschreibt, was der Chunk "
            "diskutiert und in welchem Kontext er steht. "
            "Format: 'Dieser Chunk diskutiert [Thema] im Kontext von [Oberthema] aus Paper [Titel].'"
        )

        # Paper-Kontext als user-Message mit cache_control (wird gecacht)
        paper_context = (
            f"Paper-ID: {paper_id}\n"
            f"Titel: {paper_title}\n"
            f"Abstract: {paper_abstract}"
        )

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": paper_context,
                            "cache_control": {"type": "ephemeral"},
                        },
                        {
                            "type": "text",
                            "text": f"\nChunk:\n{chunk_text}\n\nSchreibe den 1-Satz-Kontext:",
                        },
                    ],
                }
            ],
        )

        return response.content[0].text.strip()

    except Exception:
        # Graceful degradation: leerer String wenn API nicht verfuegbar
        return ""


def build_contextual_embedding_text(
    context_sentence: str,
    chunk_text: str,
) -> str:
    """Kombiniert context_sentence und chunk_text zu Embedding-Input.

    Der Kontext-Satz kommt VOR dem Chunk-Text, damit das Embedding
    den Chunk im Kontext des Papers repraesentiert.

    Args:
        context_sentence: 1-Satz-Kontext generiert von generate_context_sentence.
        chunk_text: Originaler Chunk-Text aus dem Paper.

    Returns:
        Kombinierter Text fuer Embedding: "<context_sentence> <chunk_text>"
    """
    return f"{context_sentence} {chunk_text}"
