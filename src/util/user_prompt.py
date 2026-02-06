def user_prompt(base: str, request: str) -> str:
    """
    Replaces placeholders in the base string with the given intent and
    request.

    Parameters:
    - base (str): The template string containing placeholders '{{INTENT}}' and
        '{{REQUEST}}'.
    - request (str): The specific request to insert into the template.

    Returns:
    - str: The formatted string with placeholders replaced.
    """
    return base.replace("{{REQUEST}}", request)
