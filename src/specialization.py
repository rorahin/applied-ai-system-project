"""
Specialization / style simulation for the Applied AI Music Recommendation System.

Applies constrained response styles to recommendation explanations without
changing recommendation content or scoring results. This simulates how a
fine-tuned model with a specific output persona might differ from the default
response — same underlying data, different presentation tone.

Supported styles:
    default      — original pipe-separated format, unchanged
    professional — semicolon-separated, formal phrasing
    casual       — friendlier language, same pipe structure
    technical    — adds weight annotations per scoring dimension
"""

VALID_STYLES = {"default", "professional", "casual", "technical"}


def validate_style(style: str) -> str:
    """Return style unchanged if valid; fall back to 'default' for unknown styles."""
    if style in VALID_STYLES:
        return style
    return "default"


def apply_style(explanation: str, style: str) -> str:
    """
    Reformat a scoring explanation string for the requested style.

    The explanation from score_song() is pipe-separated, e.g.:
        'genre match (rock) | mood mismatch (chill != intense) | energy 0.91 (target 0.85) | popularity 66'

    Each style transforms the presentation without altering the underlying facts.
    """
    if style == "default":
        return explanation

    parts = [p.strip() for p in explanation.split("|")]

    if style == "professional":
        return "; ".join(parts)

    if style == "casual":
        friendly = []
        for part in parts:
            part = part.replace("genre match", "genre fits")
            part = part.replace("genre mismatch", "genre doesn't quite match")
            part = part.replace("mood match", "vibe fits")
            part = part.replace("mood mismatch", "vibe is a bit off")
            part = part.replace("decade match", "from the right era")
            part = part.replace("decade mismatch", "from a different era")
            friendly.append(part)
        return " | ".join(friendly)

    if style == "technical":
        weight_map = {
            "genre":      "[w=0.30]",
            "mood":       "[w=0.30]",
            "energy":     "[w=0.20]",
            "popularity": "[w=0.10]",
            "decade":     "[w=0.10]",
        }
        annotated = []
        for part in parts:
            tag = next((weight_map[k] for k in weight_map if k in part), "")
            annotated.append(f"{part} {tag}".strip() if tag else part)
        return " | ".join(annotated)

    return explanation
