def system_prompt(base: str, choices_keys: list[str]) -> str:
    """
    Replaces placeholders in the base string with the given choices.

    Parameters:
    - base (str): The template string containing placeholders
        '{{CHOICES_KEYS}}'.
    - choices_keys (list[str]): Possible choices for the answer

    Returns:
    - str: The formatted string with placeholders replaced.
    """
    if "{{CHOICES_KEYS}}" not in base:
        raise ValueError("expected a chat which contains {{CHOICES_KEYS}}")

    return base.replace("{{CHOICES_KEYS}}", " or ".join(choices_keys))
