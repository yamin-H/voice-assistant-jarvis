"""Tool catalog for the execution layer.

A tool listed here is an allowed capability concept. In Agent mode, plans are
validated against this catalog before execution.
"""

from dataclasses import dataclass
import json


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    risk: str
    required_arguments: tuple[str, ...]
    optional_arguments: tuple[str, ...] = ()

    def validate_arguments(self, arguments):
        if not isinstance(arguments, dict):
            raise ValueError(f"{self.name} arguments must be an object.")

        allowed = set(self.required_arguments) | set(self.optional_arguments)
        unknown = set(arguments) - allowed
        missing = set(self.required_arguments) - set(arguments)

        if unknown:
            raise ValueError(
                f"{self.name} has unsupported arguments: {', '.join(sorted(unknown))}"
            )
        if missing:
            raise ValueError(
                f"{self.name} is missing arguments: {', '.join(sorted(missing))}"
            )

        for key, value in arguments.items():
            if not isinstance(value, str):
                raise ValueError(
                    f"{self.name}.{key} must be a string."
                )

    def prompt_description(self):
        required = ", ".join(self.required_arguments) or "none"
        optional = ", ".join(self.optional_arguments) or "none"

        return {
            "name": self.name,
            "description": self.description,
            "risk": self.risk,
            "required_arguments": required,
            "optional_arguments": optional,
        }


TOOLS = {
    "app.open": ToolSpec(
        name="app.open",
        description=(
            "Open a locally installed Windows application by name, or open one "
            "of the known website targets."
        ),
        risk="reversible",
        required_arguments=("target",),
    ),
    "app.list_installed": ToolSpec(
        name="app.list_installed",
        description="List or search locally installed Windows applications.",
        risk="safe",
        required_arguments=(),
        optional_arguments=("query",),
    ),
    "web.search": ToolSpec(
        name="web.search",
        description="Search the web using the current browser.",
        risk="safe",
        required_arguments=("query",),
    ),
    "window.focus": ToolSpec(
        name="window.focus",
        description="Bring an already-open application window to the front.",
        risk="reversible",
        required_arguments=("window_name",),
    ),
    "window.close": ToolSpec(
        name="window.close",
        description="Close an application window. This may discard unsaved work.",
        risk="confirm",
        required_arguments=("window_name",),
    ),
    "window.layout": ToolSpec(
        name="window.layout",
        description="Maximize, minimize, snap left, snap right, or show desktop.",
        risk="reversible",
        required_arguments=("action",),
        optional_arguments=("window_name",),
    ),
    "input.type_text": ToolSpec(
        name="input.type_text",
        description="Type literal text into the currently focused application.",
        risk="confirm",
        required_arguments=("text",),
    ),
    "input.press_key": ToolSpec(
        name="input.press_key",
        description="Press a named keyboard shortcut or key (e.g., enter, esc, ctrl+c, save).",
        risk="reversible",
        required_arguments=("key",),
    ),
    "input.scroll": ToolSpec(
        name="input.scroll",
        description="Scroll the focused window up or down.",
        risk="reversible",
        required_arguments=("direction",),
        optional_arguments=("amount",),
    ),
    "system.screenshot": ToolSpec(
        name="system.screenshot",
        description="Take a screenshot for later observation.",
        risk="safe",
        required_arguments=(),
    ),
    "notes.create": ToolSpec(
        name="notes.create",
        description="Save a local note.",
        risk="reversible",
        required_arguments=("text",),
    ),
    "notes.read": ToolSpec(
        name="notes.read",
        description="Read saved local notes.",
        risk="safe",
        required_arguments=(),
    ),
    "reminder.create": ToolSpec(
        name="reminder.create",
        description="Create a local timer, reminder, or alarm.",
        risk="reversible",
        required_arguments=("request",),
    ),
}


def tool_prompt():
    """Compact JSON catalog supplied to the model."""
    catalog = [spec.prompt_description() for spec in TOOLS.values()]
    return json.dumps(catalog, indent=2)