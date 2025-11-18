# prompts.py
from typing import List, Dict

EVAL_SYSTEM_PROMPT = """
You are a prompt quality evaluator assistant. Use the retrieved examples to judge whether a user's input is an actionable, well-formed prompt.
Return JSON ONLY in the following shape:
{
  "is_prompt": "True" or "False",
  "reason": "<short explanation 1-2 sentences>",
  "score": <0-10 numeric where 10 is perfect>
}
"""

IMPROVE_SYSTEM_PROMPT = """
You are a prompt-improvement assistant. Given a user prompt and a set of similar high-quality prompt examples, produce a single improved production-ready prompt.
Return JSON ONLY:
{
  "rating": <0-10>,
  "improved_prompt": "<the improved prompt>",
  "explanation": "<1-2 sentence explanation what you changed and why>"
}
"""


def build_eval_user_message(user_prompt: str, retrieved: List[Dict]) -> str:
    examples_text = ""
    for i, doc in enumerate(retrieved):
        meta = doc.get("metadata", {})
        examples_text += f"{i+1}) repo:{meta.get('repo')} file:{meta.get('file')}\nPROMPT: {meta.get('prompt_preview')}\nCONTEXT_SNIPPET: {doc.get('content')[:600]}\n\n"
    template = f"""
User prompt:
\"\"\"{user_prompt}\"\"\"

Retrieved examples:
{examples_text}

Question: Is the user input an actionable/real prompt in the style of the retrieved examples?
Explain briefly and return the JSON described in the system prompt.
"""
    return template


def build_improve_user_message(user_prompt: str, retrieved: List[Dict]) -> str:
    examples_text = ""
    for i, doc in enumerate(retrieved):
        meta = doc.get("metadata", {})
        examples_text += f"{i+1}) repo:{meta.get('repo')} file:{meta.get('file')}\nPROMPT: {meta.get('prompt_preview')}\nCONTEXT_SNIPPET: {doc.get('content')[:600]}\n\n"
    template = f"""
User prompt:
\"\"\"{user_prompt}\"\"\"

Here are similar high-quality prompts:
{examples_text}

Task:
1) Provide a numeric rating 0-10.
2) Return an improved prompt that is clear, contains intent, input/output spec, constraints/examples if needed.
3) Briefly (1-2 sentences) explain what you changed.

Return JSON ONLY in the shape specified in the system prompt.
"""
    return template
