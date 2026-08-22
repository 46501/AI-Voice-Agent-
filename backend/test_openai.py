import os
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')
print(f"OPENAI_API_KEY: {'PRESENT' if api_key else 'MISSING'}")

try:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[{'role': 'user', 'content': 'Say hello.'}]
    )
    print('LLM: PASS')
except Exception as e:
    print(f'LLM FAILED. Error type: {type(e).__name__}')
    print(f'LLM Error message: {str(e)}')
