import re

# Matches an entire string wrapped in triple backticks, optionally with a
# language tag.
_CODE_FENCE_RE: re.Pattern[str] = re.compile(
    r"[\s\S]*```(?:\S*)?\n(.*?)\n```[\s\S]*$",
    re.DOTALL,
)


def strip_code_fences(text: str) -> str:
    """
    If the input is wrapped in a triple-backtick code fence (optionally with a
    language), return only the inner content. Otherwise, return the text
    unchanged.

    Parameters:
        text (str): The input text, possibly fenced with ```.

    Returns:
        str: The unfenced inner content, or the original text if no full fence
            matches.

    Examples:
        >>> strip_code_fences("```\\nprint('hi')\\n```")
        "print('hi')"
        >>> strip_code_fences("```python\\nprint('hi')\\n```")
        "print('hi')"
        >>> strip_code_fences("no fences here")
        "no fences here"
    """
    m = _CODE_FENCE_RE.fullmatch(text)
    return m.group(1) if m else text


def strip_after_double_newline(text: str) -> str:
    """
    Remove everything after the first occurrence of two consecutive newlines.

    Parameters:
        text (str): The input text.

    Returns:
        str: The text up to (but not including) the first double newline,
            or the original text if no double newline is found.

    Examples:
        >>> strip_after_double_newline("first\\nsecond\\n\\nremove this")
        "first line\\nsecond line"
        >>> strip_after_double_newline("no double newline here\\nsingle only")
        "no double newline here\\nsingle only"
        >>> strip_after_double_newline("start\\n\\nmiddle\\n\\nend")
        "start"
    """
    parts = text.split("\n\n", 1)
    return parts[0] if len(parts) > 1 else text
