"""Short-lived, exact-action confirmation tokens."""

from dataclasses import dataclass
import hashlib
import json
import secrets
import time


@dataclass(frozen=True)
class ConfirmationRequest:
    token: str
    message: str
    expires_at: float

    def pretty(self):
        seconds_left = max(0, int(self.expires_at - time.monotonic()))
        return (
            f"Confirmation required: {self.message}\n"
            f"Type exactly: confirm {self.token}\n"
            f"Token expires in about {seconds_left} seconds."
        )


class ConfirmationGate:
    """Issues approvals bound to one exact tool call and its arguments."""

    def __init__(self, lifetime_seconds=60):
        self.lifetime_seconds = lifetime_seconds
        self.pending = {}

    def request(self, tool_call, message):
        token = secrets.token_urlsafe(6)
        expires_at = time.monotonic() + self.lifetime_seconds

        self.pending[token] = {
            "fingerprint": self._fingerprint(tool_call),
            "expires_at": expires_at,
        }

        return ConfirmationRequest(
            token=token,
            message=message,
            expires_at=expires_at,
        )

    def approve(self, token, tool_call):
        """Consume a token only if it matches this exact requested action."""
        pending = self.pending.pop(token, None)

        if pending is None:
            return False, "That confirmation token is unknown or was already used."

        if time.monotonic() > pending["expires_at"]:
            return False, "That confirmation token expired. Please request again."

        if pending["fingerprint"] != self._fingerprint(tool_call):
            return False, "That token does not authorize this action."

        return True, ""

    @staticmethod
    def _fingerprint(tool_call):
        payload = {
            "tool": tool_call.tool,
            "arguments": tool_call.arguments,
        }
        encoded = json.dumps(
            payload,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()