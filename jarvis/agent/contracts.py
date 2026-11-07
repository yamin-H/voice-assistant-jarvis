"""Strict, local validation for agent plans.

The model output is always untrusted. This module converts it into a validated
plan object before any future execution layer can see it.
"""

from dataclasses import dataclass
import json


VALID_MODES = {"conversation", "plan", "clarify", "reject"}


@dataclass(frozen=True)
class ToolCall:
    """One proposed step. This does not execute anything."""

    tool: str
    arguments: dict
    purpose: str
    risk: str


@dataclass(frozen=True)
class AgentPlan:
    """A validated proposal from the planner."""

    goal: str
    mode: str
    spoken_response: str
    clarification: str
    steps: list[ToolCall]

    @classmethod
    def from_dict(cls, data, tools, max_steps):
        """Validate untrusted JSON from the language model."""

        if not isinstance(data, dict):
            raise ValueError("Plan must be a JSON object.")

        required = {
            "goal",
            "mode",
            "spoken_response",
            "clarification",
            "steps",
        }
        if set(data) != required:
            raise ValueError("Plan contains missing or unexpected fields.")

        goal = data["goal"]
        mode = data["mode"]
        spoken_response = data["spoken_response"]
        clarification = data["clarification"]
        raw_steps = data["steps"]

        if not isinstance(goal, str) or not goal.strip():
            raise ValueError("Plan goal must be non-empty text.")
        if mode not in VALID_MODES:
            raise ValueError(f"Unknown plan mode: {mode}")
        if not isinstance(spoken_response, str):
            raise ValueError("spoken_response must be text.")
        if not isinstance(clarification, str):
            raise ValueError("clarification must be text.")
        if not isinstance(raw_steps, list):
            raise ValueError("steps must be a list.")
        if len(raw_steps) > max_steps:
            raise ValueError(f"Plan has more than {max_steps} steps.")

        calls = []
        for number, raw_step in enumerate(raw_steps, start=1):
            calls.append(
                _validate_step(
                    raw_step=raw_step,
                    tools=tools,
                    number=number,
                )
            )

        if mode in {"conversation", "clarify", "reject"} and calls:
            raise ValueError(f"{mode} mode must not contain tool steps.")

        if mode == "plan" and not calls:
            raise ValueError("plan mode must contain at least one step.")

        return cls(
            goal=goal.strip(),
            mode=mode,
            spoken_response=spoken_response.strip(),
            clarification=clarification.strip(),
            steps=calls,
        )

    def pretty(self):
        """Human-readable dry-run output."""
        lines = [
            f"Goal: {self.goal}",
            f"Mode: {self.mode}",
            f"Jarvis would say: {self.spoken_response or '(nothing)'}",
        ]

        if self.clarification:
            lines.append(f"Needs clarification: {self.clarification}")

        if not self.steps:
            lines.append("Proposed steps: none")
            return "\n".join(lines)

        lines.append("Proposed steps:")
        for number, step in enumerate(self.steps, start=1):
            arguments = json.dumps(step.arguments, ensure_ascii=False)
            lines.append(
                f"  {number}. {step.tool}({arguments}) "
                f"[{step.risk}] — {step.purpose}"
            )

        lines.append("Dry-run only: no step was executed.")
        return "\n".join(lines)


def _validate_step(raw_step, tools, number):
    """Validate each model-proposed step against our local tool catalog."""

    if not isinstance(raw_step, dict):
        raise ValueError(f"Step {number} must be an object.")

    required = {"tool", "arguments_json", "purpose"}
    if set(raw_step) != required:
        raise ValueError(f"Step {number} contains missing or unexpected fields.")

    tool_name = raw_step["tool"]
    arguments_json = raw_step["arguments_json"]
    purpose = raw_step["purpose"]

    if tool_name not in tools:
        raise ValueError(f"Step {number} requested unknown tool: {tool_name}")
    if not isinstance(arguments_json, str):
        raise ValueError(f"Step {number} arguments_json must be text.")
    if not isinstance(purpose, str) or not purpose.strip():
        raise ValueError(f"Step {number} purpose must be non-empty text.")

    try:
        arguments = json.loads(arguments_json)
    except json.JSONDecodeError as error:
        raise ValueError(f"Step {number} arguments are not valid JSON.") from error

    if not isinstance(arguments, dict):
        raise ValueError(f"Step {number} arguments must be a JSON object.")

    spec = tools[tool_name]
    spec.validate_arguments(arguments)

    return ToolCall(
        tool=tool_name,
        arguments=arguments,
        purpose=purpose.strip(),
        risk=spec.risk,
    )