"""What the assistant says and does in response to you."""
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class Reply:
    text: str                                   # what Jarvis says
    action: Optional[Callable[[], None]] = None  # runs right after Jarvis starts speaking
    quit: bool = False                          # True = stop the program after speaking
    # If set, text is a yes/no question. This runs only if you answer "yes".
    # It can return a sentence to speak afterwards.
    on_yes: Optional[Callable[[], Optional[str]]] = None