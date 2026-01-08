import os
import json
from openai import OpenAI


# تهيئة العميل
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Prompt ثابت
SYSTEM_PROMPT = """You are an intent extraction engine.

Your job is to analyze a user's search query and extract structured intent data.

You must:
- Understand Arabic (formal and dialect), English, or mixed text.
- Handle spelling mistakes and phonetic writing.
- Infer the most likely intent and domain.
- Output ONLY valid JSON.
- Never ask questions.
- Never explain.
- Never add extra text.

If the input is a greeting, irrelevant, or unclear, set intent = "unknown".
Use confidence score between 0.0 and 1.0.

Allowed intent values: travel, product, service, unknown.
Allowed domain examples:
- travel.flight
- product.smartphone
- product.laptop
- product.clothing
- product.furniture
- service.internet_home
- service.insurance
If not sure, domain must be null.

Allowed priority values:
cheapest, best_value, top_rated, most_popular, fastest, newest, or null.

Output JSON format:
{
  "intent": "...",
  "domain": "... or null",
  "entities": { ... },
  "priority": "... or null",
  "confidence": 0.0
}
"""

def _safe_json(text: str) -> dict:
    # بعض الأحيان يرجع النص داخل ```json ... ```
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`")
        # إزالة كلمة json إن وجدت
        t = t.replace("json", "", 1).strip()
    return json.loads(t)

def parse_intent(user_input: str) -> dict:
    if not os.getenv("OPENAI_API_KEY"):
        # لا نكسر التطبيق: رجّع unknown واضح
        return {
            "intent": "unknown",
            "domain": None,
            "entities": {},
            "priority": None,
            "confidence": 0.1
        }

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f'Extract intent from this user input:\n\n"{user_input}"'}
            ],
        )
        content = resp.choices[0].message.content or "{}"
        data = _safe_json(content)

        # ضمان مفاتيح أساسية
        return {
            "intent": data.get("intent", "unknown"),
            "domain": data.get("domain", None),
            "entities": data.get("entities", {}) or {},
            "priority": data.get("priority", None),
            "confidence": float(data.get("confidence", 0.0) or 0.0)
        }
    except Exception as e:
        # في حال أي خطأ: نرجع unknown بدل ما نطيح السيرفر
        return {
            "intent": "unknown",
            "domain": None,
            "entities": {"_error": str(e)},
            "priority": None,
            "confidence": 0.1
        }
