from groq import Groq
import os
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    max_tokens=100,
    messages=[
        {"role": "user", "content": "Say hello!"}
    ],
)

print(response.choices[0].message.content)