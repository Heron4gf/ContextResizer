from openai import OpenAI
from dotenv import load_dotenv
from utils import chars_to_tokens, tokens_to_chars

load_dotenv()

client = OpenAI()

def summarize(text: str, max_tokens_size: int) -> str:
    current_chars = len(text)
    current_tokens = chars_to_tokens(current_chars)

    if current_tokens <= max_tokens_size:
        return text

    expected_chars = tokens_to_chars(max_tokens_size)

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {
                "role": "developer",
                "content": f"Summarize the following text to approximately {expected_chars} characters. Return only the summary without any additional text."
            },
            {
                "role": "user",
                "content": text
            }
        ],
        max_tokens=max_tokens_size
    )
    return response.choices[0].message.content
