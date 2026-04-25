import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

from database import db
from utils.logger import get_logger
import config

log = get_logger("creative.copy_generator")

PROMPTS_DIR = Path(__file__).parent / "prompts"


@dataclass
class CopyVariation:
    headline: str
    body: str
    cta: str
    hook: str = ""
    compliance_note: str = ""


def generate_copy(
    product: str,
    audience: str,
    tone: str = "professional",
    objective: str = "traffic",
    count: int = 3,
    existing_ad_texts: list = None,
) -> list[CopyVariation]:
    if not config.ANTHROPIC_API_KEY:
        log.error("ANTHROPIC_API_KEY not set. AI copy generation is disabled.")
        print("\nTo use AI copy generation, add ANTHROPIC_API_KEY to your .env file.")
        print("Alternatively, create ads manually: python main.py ad create --headline '...' --body '...'")
        return []

    try:
        import anthropic
    except ImportError:
        log.error("anthropic package not installed. Run: pip install anthropic")
        return []

    prompt = _build_prompt(product, audience, tone, objective, count, existing_ad_texts)

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=config.CLAUDE_MAX_TOKENS_COPY,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        variations = _parse_response(raw)
        _save_variations(variations, product, audience, tone, objective)
        return variations
    except Exception as e:
        log.error(f"Claude API error: {e}")
        return []


def _build_prompt(product, audience, tone, objective, count, existing_ad_texts) -> str:
    template_path = PROMPTS_DIR / "ad_copy.txt"
    if template_path.exists():
        template = template_path.read_text(encoding="utf-8")
    else:
        template = _default_prompt_template()

    existing_instruction = ""
    if existing_ad_texts:
        existing_instruction = f"Avoid repeating these existing ads:\n" + "\n".join(f"- {t}" for t in existing_ad_texts)

    return template.format(
        count=count,
        product=product,
        audience=audience,
        tone=tone,
        objective=objective,
        brand_name=config.BRAND_NAME,
        landing_url=config.DEFAULT_LANDING_URL,
        existing_ads_instruction=existing_instruction,
    )


def _default_prompt_template() -> str:
    return """You are an expert Meta Ads copywriter. Generate {count} high-converting Facebook/Instagram ad copy variations.

PRODUCT/SERVICE: {product}
TARGET AUDIENCE: {audience}
CAMPAIGN OBJECTIVE: {objective}
TONE: {tone}
BRAND: {brand_name}
LANDING PAGE: {landing_url}

{existing_ads_instruction}

For each variation output EXACTLY this JSON structure (no extra text, just JSON):
{{
  "variations": [
    {{
      "headline": "Max 40 characters. Attention-grabbing, benefit-focused.",
      "body": "Max 125 characters. Problem to Solution to Proof structure.",
      "cta": "One of: LEARN_MORE, SHOP_NOW, SIGN_UP, GET_QUOTE, DOWNLOAD, CONTACT_US, APPLY_NOW",
      "hook": "First 3 words optimized for scroll-stop",
      "compliance_note": "Flag if any claim needs substantiation, else empty string"
    }}
  ]
}}

RULES:
- Headlines must be under 40 characters
- Body must be under 125 characters
- Each variation must use a different psychological angle
- No superlatives without proof ("best", "fastest") unless backed by data
- Follow: Pain point or desire → Your solution → Social proof or urgency"""


def _parse_response(raw: str) -> list[CopyVariation]:
    # Strip markdown code fences if present
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    try:
        data = json.loads(raw)
        variations = data.get("variations", [])
        result = []
        for v in variations:
            result.append(CopyVariation(
                headline=v.get("headline", "")[:40],
                body=v.get("body", "")[:125],
                cta=v.get("cta", "LEARN_MORE"),
                hook=v.get("hook", ""),
                compliance_note=v.get("compliance_note", ""),
            ))
        return result
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse Claude response as JSON: {e}")
        log.debug(f"Raw response: {raw[:500]}")
        return []


def _save_variations(variations: list[CopyVariation], product, audience, tone, objective):
    for v in variations:
        db.save_copy({
            "product": product,
            "audience": audience,
            "tone": tone,
            "objective": objective,
            "headline": v.headline,
            "body": v.body,
            "cta": v.cta,
            "hook": v.hook,
            "compliance_note": v.compliance_note,
            "model": config.CLAUDE_MODEL,
        })
    log.info(f"Saved {len(variations)} copy variations to database.")
