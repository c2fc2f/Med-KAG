def user_prompt(base: str, request: str, choices: dict[str, str]) -> str:
    """
    Replaces placeholders in the base string with the given intent and
    request.

    Parameters:
    - base (str): The template string containing placeholders '{{INTENT}}',
        '{{REQUEST}}' and '{{CHOICES}}'.
    - request (str): The specific request to insert into the template.
    - choices (dict[str, str]): Possible choices for the answer

    Returns:
    - str: The formatted string with placeholders replaced.
    """
    if "{{REQUEST}}" not in base:
        raise ValueError("expected a chat which contains {{REQUEST}}")

    if "{{CHOICES}}" not in base:
        raise ValueError("expected a chat which contains {{CHOICES}}")

    return base.replace("{{REQUEST}}", request).replace(
        "{{CHOICES}}",
        "\n".join(f"{key}: {value}" for key, value in choices.items()),
    )
