import os
import json
from groq import Groq
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


def _get_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except:
        import os
        return os.getenv("GROQ_API_KEY", "")

client = Groq(api_key=_get_key())
GENERATE_PROMPT = """
You are an interview question generator.

Generate EXACTLY {count} interview questions. Not more, not less.
Role: {role}
Experience Level: {level}
Focus Area: {focus}

IMPORTANT: The "questions" array must contain EXACTLY {count} items.

Respond ONLY with valid JSON, no extra text:
{{
  "questions": [
    {{
      "id": 1,
      "category": "Behavioral",
      "question": "..."
    }}
  ]
}}
"""

def generate_questions(role, level, focus, count=5):
    prompt = GENERATE_PROMPT.format(
        role=role,
        level=level,
        focus=focus,
        count=count
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)
    return data["questions"]