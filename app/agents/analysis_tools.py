import re
import unicodedata
from typing import Annotated, List

from langchain.tools import tool

from app import crud
from app.agents import portfolio_analyzer_agent
from app.agents.toolkit_common import require_context


@tool
def get_full_portfolio_analysis() -> List[dict] | str:
    """Return analysis for all assets in the active portfolio."""
    try:
        context = require_context()
        assets = crud.get_assets(context.db_session, portfolio_id=context.portfolio_id)
        if not assets:
            return "Error: No assets found in the portfolio to analyze."
        return [portfolio_analyzer_agent.analyze_asset(context.db_session, asset).model_dump(mode="json") for asset in assets]
    except ValueError as exc:
        return f"An unexpected error occurred during portfolio analysis: {exc}"


@tool
def classify_agent_request(
    question: Annotated[str, "The original natural-language request from the user."],
) -> dict:
    """Classify a request into registration, management, or analysis."""
    normalized = unicodedata.normalize("NFKD", question.lower())
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    tokens = re.findall(r"[a-z0-9]+", normalized)

    root_patterns = {
        "registration_agent": [
            "registr",
            "cadast",
            "compr",
            "buy",
            "acqui",
            "purch",
            "dividend",
            "dividendo",
            "distribu",
            "jcp",
        ],
        "management_agent": [
            "updat",
            "atualiz",
            "actualiz",
            "correct",
            "corrig",
            "correg",
            "sell",
            "vend",
            "delet",
            "elimin",
            "adjust",
            "ajust",
            "fix",
            "consert",
            "edit",
        ],
        "analysis_agent": [
            "anal",
            "invest",
            "recomend",
            "recommend",
            "sugest",
            "suger",
        ],
    }

    phrase_patterns = {
        "registration_agent": ["add position", "new asset"],
        "analysis_agent": ["where should", "onde devo", "donde deber"],
    }

    scores = {agent: 0 for agent in root_patterns}
    matched_roots = {agent: [] for agent in root_patterns}
    matched_phrases = {agent: [] for agent in root_patterns}

    for agent, roots in root_patterns.items():
        for token in tokens:
            matched_root = next((root for root in roots if token.startswith(root)), None)
            if matched_root is not None:
                scores[agent] += 1
                matched_roots[agent].append(matched_root)

    for agent, phrases in phrase_patterns.items():
        for phrase in phrases:
            if phrase in normalized:
                scores[agent] += 1
                matched_phrases[agent].append(phrase)

    best_agent = max(scores, key=scores.get)
    best_score = scores[best_agent]
    total_hits = sum(scores.values()) or 1
    confidence = min(1.0, best_score / total_hits) if best_score else 0.33

    if best_score:
        roots_used = sorted(set(matched_roots[best_agent]))
        phrases_used = sorted(set(matched_phrases[best_agent]))
        evidence_parts = []
        if roots_used:
            evidence_parts.append(f"roots={roots_used}")
        if phrases_used:
            evidence_parts.append(f"phrases={phrases_used}")
        evidence = "; ".join(evidence_parts) if evidence_parts else "no explicit evidence"
        reasoning = f"Matched routing signals for {best_agent}: {best_score} hit(s); {evidence}."
    else:
        reasoning = "No strong routing signals; defaulting to analysis_agent."
    return {
        "agent_name": best_agent if best_score else "analysis_agent",
        "confidence": round(confidence, 2),
        "reasoning": reasoning,
    }
