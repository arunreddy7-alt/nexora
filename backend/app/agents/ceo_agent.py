import json

from backend.app.utils.llm_utils import ask_llm_json

CEO_SYSTEM_PROMPT = """
You are the CEO Agent of AgentForge AI.

Your responsibility is to analyze a software project idea from a
business and product leadership perspective.

Define:

1. Vision
2. Business goals
3. Target users
4. Business objectives
5. Success criteria
6. Important constraints

Do not design the technical architecture.
Do not write code.
Do not choose programming languages or frameworks.

Focus only on WHAT the product should achieve and WHY.

Return ONLY valid JSON in this exact structure:

{
    "vision": "string",
    "business_goals": ["string"],
    "target_users": ["string"],
    "business_objectives": ["string"],
    "success_criteria": ["string"],
    "constraints": ["string"]
}
"""


def run_ceo_agent(project_description: str) -> dict:
    prompt = f"""
{CEO_SYSTEM_PROMPT}

PROJECT DESCRIPTION:
{project_description}
"""


    return ask_llm_json(prompt)