def snake_to_sentence(text: str) -> str:
    """Convert snake_case string into 'Snake case' sentence."""
    return text.replace('_', ' ').lower().capitalize()
