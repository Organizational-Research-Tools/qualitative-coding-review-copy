"""Small unchanged extraction from the prompt generator used in the empirical study.

Attribution is withheld for anonymous review.
"""

def format_segment_context(context: dict) -> str:
    """Format segment context for prompt injection.

    Formats the segment's position within the campaign document and
    shows preceding/following segment titles to provide argumentative
    context for coding.

    Args:
        context: Dict with 'position', 'preceding_titles', 'following_title'

    Returns:
        Formatted context string, or empty string if no context
    """
    if not context:
        return ""

    lines = []

    # Position in document
    position = context.get('position', '')
    if position:
        lines.append(f"Position: Segment {position}")

    # Preceding section titles
    preceding = context.get('preceding_titles', [])
    if preceding:
        lines.append("Preceding sections:")
        for title in preceding:
            lines.append(f"  • {title}")

    # Following section title
    following = context.get('following_title')
    if following:
        lines.append(f"Following section: {following}")

    return '\n'.join(lines) if lines else ""
