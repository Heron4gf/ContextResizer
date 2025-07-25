
CHAR_TO_TOKEN = 0.75

def chars_to_tokens(chars: int) -> int:
    return round(chars * CHAR_TO_TOKEN)

def tokens_to_chars(tokens: int) -> int:
    return round(tokens / CHAR_TO_TOKEN)