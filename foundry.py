"""Minimal Azure OpenAI Foundry integration with evidence validation."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from engine import Insight


SYSTEM = """You are a football studio insights editor. Facts describe a wholly synthetic match.
Return ONLY one JSON object with keys overlay, casual, analyst, evidence_ids.
Overlay: maximum 18 words. Casual: maximum 35 words. Analyst: maximum 60 words.
Use only supplied facts. Evidence IDs must be chosen from the supplied IDs.
Distinguish observation from interpretation. Use cautious language for tactical inference.
Do not claim that one event caused another, predict a goal, invent scores or players,
or describe video footage. Never use web search. No markdown."""


def configured() -> bool:
    return bool(os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"))


def _request(messages: list[dict]) -> dict:
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    if endpoint.endswith("/openai/v1"):
        endpoint = endpoint[:-len("/openai/v1")]
    url = endpoint + "/openai/v1/chat/completions"
    payload = {
        "model": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        "messages": messages,
        "reasoning_effort": "minimal",
        "max_completion_tokens": 650,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "api-key": os.environ["AZURE_OPENAI_API_KEY"]},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read(500).decode("utf-8", errors="replace")
        raise RuntimeError(f"Foundry HTTP {exc.code}: {detail}") from exc


def _parse_json(content: str) -> dict:
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    return json.loads(content)


def narrate(insight: Insight) -> dict:
    if not configured():
        return fallback(insight, "Foundry credentials are not configured")
    try:
        response = _request([
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps({
                "kind": insight.kind,
                "facts": insight.facts,
                "allowed_evidence_ids": insight.evidence_ids,
            })},
        ])
        raw = response["choices"][0]["message"]["content"]
        parsed = _parse_json(raw)
        allowed = set(insight.evidence_ids)
        ids = parsed.get("evidence_ids")
        if (not isinstance(ids, list) or not ids or
                not all(isinstance(item, str) for item in ids) or
                not set(ids) <= allowed):
            raise ValueError("Model returned missing or unknown evidence IDs")
        for key, limit in (("overlay", 18), ("casual", 35), ("analyst", 60)):
            if not isinstance(parsed.get(key), str) or not parsed[key].strip():
                raise ValueError(f"Missing {key}")
            if len(parsed[key].split()) > limit:
                raise ValueError(f"{key} exceeds word limit")
        return {"source": "Microsoft Foundry · gpt-5-mini",
                "overlay": parsed["overlay"], "casual": parsed["casual"],
                "analyst": parsed["analyst"], "evidence_ids": ids,
                "usage": response.get("usage", {})}
    except (ValueError, KeyError, IndexError, TypeError, TimeoutError, OSError, RuntimeError) as exc:
        return fallback(insight, str(exc))


def fallback(insight: Insight, reason: str) -> dict:
    if insight.kind == "pressure_surge":
        overlay = "Red FC's high press is producing more recoveries."
        casual = "Red FC is winning the ball near Blue FC's goal more often than before."
        analyst = ("Red FC recorded three high recoveries and seven attacking-third pressures "
                   "from 25:00–29:59, versus zero high recoveries and one pressure in the prior window. "
                   "Blue FC also had four failed exits; these events suggest a more disruptive high press.")
    else:
        overlay = "Blue FC is finding a route through the press."
        casual = "Blue FC is moving the ball forward again after a difficult spell."
        analyst = ("Blue FC completed nine progressive passes from 30:00–34:59 while Red FC "
                   "recorded no high recoveries, down from three in the previous window. "
                   "This suggests Blue FC may have found an effective way past the press.")
    return {"source": "Local fallback · Foundry unavailable", "overlay": overlay,
            "casual": casual, "analyst": analyst,
            "evidence_ids": list(insight.evidence_ids), "reason": reason}


def recap(insights: list[dict]) -> dict:
    # A fixed recap is available even when cloud inference is unavailable.
    local = ("Red FC's pressure rose after 25:00, with three high recoveries and seven "
             "attacking-third pressures in five minutes. Blue FC then completed nine "
             "progressive passes while Red FC's high recoveries dropped to zero. "
             "The synthetic segment shows a press and a possible response to it.")
    if not configured():
        return {"text": local, "source": "Local fallback · Foundry unavailable"}
    try:
        response = _request([
            {"role": "system", "content": "Write a 65-word maximum recap of a synthetic football segment. "
             "Use only the JSON facts. Describe observations and cautious tactical interpretations. "
             "Do not invent score, result, players, or causality."},
            {"role": "user", "content": json.dumps([i.facts for i in insights])},
        ])
        text = response["choices"][0]["message"]["content"].strip()
        if not text or len(text.split()) > 65:
            raise ValueError("Invalid recap length")
        return {"text": text, "source": "Microsoft Foundry · gpt-5-mini"}
    except (ValueError, KeyError, IndexError, TimeoutError, OSError, RuntimeError):
        return {"text": local, "source": "Local fallback · Foundry unavailable"}
