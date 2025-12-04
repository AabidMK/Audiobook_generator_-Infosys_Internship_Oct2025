# enrich.py

def enrich_text(text: str) -> str:
    """
    Simple text enrichment to make speech more natural.
    You can improve this later using AI models.
    """
    if not text or not text.strip():
        return "No readable text found in the uploaded document."

    enriched = text.replace("\n", ". ")
    enriched = " ".join(enriched.split())  # clean extra spaces

    # Basic enhancement to sound better in speech
    enriched = (
        "Here is your audiobook version. " +
        enriched +
        " Thank you for using our audiobook generator."
    )

    return enriched
