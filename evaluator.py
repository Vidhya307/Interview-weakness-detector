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

EVAL_PROMPT = """
You are an expert interview coach. Evaluate the candidate's answer below.

Score on these 5 dimensions (1.0 to 5.0):
1. Clarity       - Easy to understand?
2. Specificity   - Uses concrete examples?
3. Relevance     - Actually answers the question?
4. Structure     - Well organised (STAR format)?
5. Impact        - Leaves strong impression?

Question: {question}
Category: {category}
Answer: {answer}

Respond ONLY with valid JSON, nothing else:
{{
  "scores": {{
    "clarity": <float>,
    "specificity": <float>,
    "relevance": <float>,
    "structure": <float>,
    "impact": <float>
  }},
  "overall": <float>,
  "weaknesses": ["<weakness 1>", "<weakness 2>"],
  "strengths": ["<strength 1>"],
  "tip": "<one actionable improvement tip>",
  "ideal_answer": "<a model answer showing exactly how to answer this question well, using STAR format where relevant, 4-6 sentences>"
}}
"""

def evaluate_answer(question, category, answer):
    prompt = EVAL_PROMPT.format(
        question=question,
        category=category,
        answer=answer
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find('{')
        end = raw.rfind('}')
        if start != -1 and end != -1:
            return json.loads(raw[start:end+1])
        raise ValueError(f"Unable to parse evaluation response. Raw output:\n{raw}")