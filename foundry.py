"""Foundry editorial agent: grounded wording, audience language, and overlay focus."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request
from pathlib import Path


SYSTEM = """You are the editorial agent for a synthetic football match overlay.
Input is a verified candidate from a deterministic event engine.
Return only a JSON object with: overlay_en, overlay_es, casual_en, casual_es,
analyst_en, analyst_es, why, focus_event_id, evidence_ids, visual_kind.
visual_kind must be pressure_zone or pass_lane. Pick focus_event_id from the
allowed evidence_ids. evidence_ids must be a nonempty subset of allowed IDs.
Overlay text is at most 14 words in each language; casual at most 35; analyst
at most 55. Say what was observed, then cautious tactical meaning. No score,
goals, predictions, invented players, live footage claims, or facts outside
the packet. The Spanish should express the same facts, not introduce others."""


def configured() -> bool:
    return bool(os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"))


def _tls_context() -> ssl.SSLContext:
    """Use macOS's CA bundle when a Python.org install has none configured."""
    context = ssl.create_default_context()
    if not context.get_ca_certs():
        system_bundle = Path("/etc/ssl/cert.pem")
        if system_bundle.is_file():
            context = ssl.create_default_context(cafile=str(system_bundle))
    return context


def _request(candidate: dict) -> dict:
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    if endpoint.endswith("/openai/v1"):
        endpoint = endpoint[:-len("/openai/v1")]
    payload = {"model": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
               "messages": [{"role": "system", "content": SYSTEM},
                            {"role": "user", "content": json.dumps(candidate)}],
               "reasoning_effort": "minimal", "max_completion_tokens": 850}
    req = urllib.request.Request(
        endpoint + "/openai/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json",
                 "api-key": os.environ["AZURE_OPENAI_API_KEY"]},
        method="POST")
    with urllib.request.urlopen(req, timeout=18, context=_tls_context()) as response:
        return json.load(response)


def validate(candidate: dict, output: dict) -> dict:
    if not isinstance(output, dict):
        raise ValueError("Expected an object")
    allowed = set(candidate["evidence_ids"])
    ids = output.get("evidence_ids")
    if not isinstance(ids, list) or not ids or not set(ids) <= allowed:
        raise ValueError("Ungrounded evidence IDs")
    if output.get("focus_event_id") not in allowed:
        raise ValueError("Focus event is not evidence")
    if output.get("visual_kind") not in ("pressure_zone", "pass_lane"):
        raise ValueError("Unsupported visual kind")
    for field, limit in (("overlay_en", 14), ("overlay_es", 14),
                         ("casual_en", 35), ("casual_es", 35),
                         ("analyst_en", 55), ("analyst_es", 55),
                         ("why", 45)):
        value = output.get(field)
        if not isinstance(value, str) or not value.strip() or len(value.split()) > limit:
            raise ValueError(f"Invalid {field}")
    return {key: output[key] for key in (
        "overlay_en", "overlay_es", "casual_en", "casual_es",
        "analyst_en", "analyst_es", "why", "focus_event_id",
        "evidence_ids", "visual_kind")}


def fallback(candidate: dict, reason: str = "") -> dict:
    if candidate["kind"] == "pressure_turn":
        data = {
            "overlay_en": "Red's press traps Blue near its own goal",
            "overlay_es": "La presión roja encierra al Azul cerca de su portería",
            "casual_en": "Red closes down Blue near its goal. Blue's attempted escape is intercepted, giving Red the ball in a dangerous area.",
            "casual_es": "Rojo presiona al Azul cerca de su portería. Intercepta su intento de salir y recupera el balón en una zona peligrosa.",
            "analyst_en": "Two Red pressures in Blue's defensive third followed a baseline with none. Blue then lost one attempted exit and Red recovered the ball high. This sequence suggests the press disrupted Blue's build-up.",
            "analyst_es": "Hubo dos presiones rojas en el tercio defensivo azul, frente a ninguna antes. Azul falló una salida y Rojo recuperó arriba. La secuencia sugiere que la presión dificultó la construcción.",
            "why": "Two close-range pressure tags, an intercepted pass, and a high recovery support the overlay.",
            "visual_kind": "pressure_zone",
        }
    else:
        data = {
            "overlay_en": "Blue plays through the press",
            "overlay_es": "Azul supera la presión con pases",
            "casual_en": "Blue finds two forward passes after restarting. The ball is moving away from its own goal again.",
            "casual_es": "Azul completa dos pases hacia adelante tras reanudar. El balón vuelve a alejarse de su portería.",
            "analyst_en": "Blue completes two passes advancing at least 12 metres after the restart, while Red has no further high recovery in this window. This suggests Blue found a route through the press.",
            "analyst_es": "Azul completa dos pases de al menos 12 metros hacia adelante tras reanudar, sin otra recuperación alta de Rojo en esta ventana. Esto sugiere una salida ante la presión.",
            "why": "Two completed forward passes, each advancing at least 12 metres, support the overlay.",
            "visual_kind": "pass_lane",
        }
    return {**data, "focus_event_id": candidate["focus_event_id"],
            "evidence_ids": candidate["evidence_ids"],
            "source": "Local editorial fallback", "reason": reason}


def edit(candidate: dict) -> dict:
    if not configured():
        return fallback(candidate, "Foundry credentials unavailable")
    try:
        response = _request(candidate)
        raw = response["choices"][0]["message"]["content"].strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0]
        output = validate(candidate, json.loads(raw))
        return {**output, "source": "Microsoft Foundry · gpt-5-mini",
                "usage": response.get("usage", {})}
    except (ValueError, KeyError, IndexError, TypeError, OSError,
            TimeoutError, urllib.error.URLError) as error:
        return fallback(candidate, str(error)[:180])
