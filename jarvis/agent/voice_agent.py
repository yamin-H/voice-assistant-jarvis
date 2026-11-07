"""Voice-facing wrapper around the planner and restricted executor.

This module holds pending spoken confirmations. It never treats arbitrary
speech as approval: only a short affirmative response while a specific action
is pending can approve that exact action.
"""

import re

from jarvis.agent.executor import ToolExecutor
from jarvis.agent.planner import AgentPlanner
from jarvis.ui_server import hub


def _label(step):
    # I haven't seen your step class, so adjust this to its real field names.
    return str(getattr(step, "tool", None) or getattr(step, "name", None) or step)[:60]


YES = re.compile(
    r"^(?:yes|yeah|yep|yup|sure|okay|ok|confirm|do it|go ahead|affirmative)$",
    re.IGNORECASE,
)

NO = re.compile(
    r"^(?:no|nope|nah|cancel|stop|never mind|nevermind|do not|don't)$",
    re.IGNORECASE,
)


class VoiceAgent:
    """Plans and executes restricted agent actions from spoken requests."""

    def __init__(self, cfg, ctx=None):
        self.planner = AgentPlanner(cfg)
        self.executor = ToolExecutor(cfg, ctx=ctx)
        self.pending_step = None
        self.pending_token = None
        self._tool_id = 0

    @property
    def awaiting_confirmation(self):
        return self.pending_step is not None

    def _exec(self, step, **kwargs):
        """Run one step and report it to the UI before and after."""
        self._tool_id += 1
        sid = self._tool_id
        hub.emit("tool", id=sid, label=_label(step), status="running")
        result = self.executor.run_step(step, **kwargs)
        hub.emit("tool", id=sid, label=_label(step), status=result.status,
                 summary=result.summary or "")
        return result

    def handle(self, text, cancel_event):
        """Return one concise sentence that Jarvis can speak aloud."""

        if self.awaiting_confirmation:
            return self._handle_confirmation(text, cancel_event)

        if cancel_event.is_set():
            return "Canceled."

        try:
            plan = self.planner.plan(text)
        except Exception as error:
            print(f"  [agent planning error] {error}")
            return "Sorry, I could not understand that request right now."

        if plan.mode == "conversation":
            return plan.spoken_response or "I am here."

        if plan.mode == "clarify":
            return plan.clarification or plan.spoken_response or "Could you clarify that?"

        if plan.mode == "reject":
            return plan.spoken_response or "I cannot do that with my current tools."

        return self._run_plan(plan, cancel_event)

    def cancel_pending(self):
        """Forget a pending confirmation without doing anything."""
        hub.emit("confirm", message=None)
        self.pending_step = None
        self.pending_token = None

    def _handle_confirmation(self, text, cancel_event):
        spoken = text.strip()

        if NO.match(spoken):
            self.cancel_pending()
            return "Okay, I canceled that action."

        if not YES.match(spoken):
            return "I am waiting for a yes or no. You can also say cancel."

        if cancel_event.is_set():
            self.cancel_pending()
            return "Canceled."

        step = self.pending_step
        token = self.pending_token
        self.cancel_pending()

        result = self._exec(step, confirmation_token=token)
        return self._speakable_result(result)

    def _run_plan(self, plan, cancel_event):
        summaries = []

        for step in plan.steps:
            if cancel_event.is_set():
                return "Canceled."

            result = self._exec(step)

            if result.status == "needs_confirmation":
                self.pending_step = step
                self.pending_token = result.confirmation.token
                hub.emit("confirm", message=result.confirmation.message)

                return (
                    f"{result.confirmation.message} "
                    "Say yes to continue, or no to cancel."
                )

            summaries.append(self._speakable_result(result))

            if result.status != "succeeded":
                return summaries[-1]

            if not result.verified:
                return (
                    f"{summaries[-1]} I stopped because I could not verify "
                    "the result."
                )

        return " ".join(summary for summary in summaries if summary) or "Done."

    @staticmethod
    def _speakable_result(result):
        """Turn low-level result records into short voice-friendly feedback."""

        if result.status == "succeeded":
            return result.summary

        if result.status == "blocked":
            return f"I stopped. {result.summary}"

        if result.status == "failed":
            return f"That did not work. {result.summary}"

        if result.status == "needs_confirmation":
            return result.confirmation.message

        return result.summary or "I stopped."