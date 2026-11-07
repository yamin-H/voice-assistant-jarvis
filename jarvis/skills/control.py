"""A shared stop button. Set when you interrupt, so typing and steps stop quickly."""
import threading

CANCEL = threading.Event()