"""Dry-run Groq planner.

This module may ask Groq to understand a request, but it never invokes a tool.
"""

import json
import os

from groq import Groq

from jarvis.agent.contracts import AgentPlan
from jarvis.agent.tools import TOOLS, tool_prompt


PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "goal": {
            "type": "string",
        },
        "mode": {
            "type": "string",
            "enum": ["conversation", "plan", "clarify", "reject"],
        },
        "spoken_response": {
            "type": "string",
        },
        "clarification": {
            "type": "string",
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tool": {
                        "type": "string",
                        "enum": list(TOOLS.keys()),
                    },
                    "arguments_json": {
                        "type": "string",
                    },
                    "purpose": {
                        "type": "string",
                    },
                },
                "required": ["tool", "arguments_json", "purpose"],
                "additionalProperties": False,
            },
        },
    },
    "required": [
        "goal",
        "mode",
        "spoken_response",
        "clarification",
        "steps",
    ],
    "additionalProperties": False,
}


PLANNER_PROMPT = """You are Jarvis's planning component.

Your job is to understand the user's intent and return a safe, structured
proposal. You do not execute anything. Never claim that an action happened.

Rules:
- This is DRY-RUN planning only. No action can happen in this phase.
- Never claim or imply that an action has already happened.
- When discussing a proposed action, use conditional language such as
  "I would..." or "I can prepare a plan to...". Do not say "I'll do it"
  or "Sure, I will..." because nothing is being executed.

- First decide whether the user's goal can be completed using only the
  available tool catalog.
- If any essential capability is absent from the catalog, use mode "reject".
  Explain briefly which capability is unavailable. Do not ask for details,
  credentials, addresses, confirmation, or any other information for an
  unavailable capability.
- Examples of unavailable capabilities include sending email or messages,
  logging into accounts, purchasing items, editing files, downloading files,
  or controlling a web page, unless a matching tool is explicitly present.

- Use mode "conversation" for ordinary questions or casual conversation.
- Use mode "clarify" only when the goal is achievable with available tools,
  but essential information is missing or genuinely ambiguous.
- Use mode "plan" only when the requested task can be represented entirely
  by one or more available tools.
- app.list_installed is an available read-only tool. Use it when the user asks
  what applications are installed, which apps match a category, or asks to
  find installed apps by name.
- Example: "What installed apps match video?" must use mode "plan" with one
  app.list_installed step whose arguments_json is:
  "{\"query\":\"video\"}".
- Example: "What apps are installed?" must use mode "plan" with one
  app.list_installed step whose arguments_json is "{}".
- Use only tools from the catalog.
- Every arguments_json value must be a valid JSON object encoded as a string.
- Each step must be necessary, concrete, and independently understandable.
- Do not invent application state, search results, file names, account data,
  web-page contents, or successful action results.
- Do not create more than the stated maximum number of steps.
- For "confirm" tools, propose the step but state clearly that confirmation
  will be required before any future execution.
- Keep spoken_response short and natural for speech.
- clarification must be an empty string unless mode is "clarify".
- steps must be an empty list unless mode is "plan".

Available tools:
{catalog}
"""


class AgentPlanner:
    """Turns a natural-language request into a locally validated dry-run plan."""

    def __init__(self, cfg):
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY is not set.")

        self.client = Groq(api_key=api_key)
        self.model = cfg["brain"]["groq"]["model"]
        self.max_steps = cfg["agent"]["max_steps"]

        self.system_prompt = PLANNER_PROMPT.replace(
           "{catalog}",
           tool_prompt(),
        )

    def plan(self, user_text):
        """Return a validated plan. This method has no execution capability."""

        user_text = user_text.strip()
        if not user_text:
            raise ValueError("Please provide a request to plan.")

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {
                    "role": "user",
                    "content": (
                        f"Maximum allowed steps: {self.max_steps}\n"
                        f"User request: {user_text}"
                    ),
                },
            ],
            temperature=0,
            max_completion_tokens=900,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "jarvis_dry_run_plan",
                    "strict": True,
                    "schema": PLAN_SCHEMA,
                },
            },
        )

        content = response.choices[0].message.content or ""
        try:
            raw_plan = json.loads(content)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                "Groq returned invalid plan JSON despite structured output."
            ) from error

        return AgentPlan.from_dict(
            data=raw_plan,
            tools=TOOLS,
            max_steps=self.max_steps,
        )