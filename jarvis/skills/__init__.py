"""All skills. Importing this package loads (and registers) every skill file.

The order matters: the first skill that understands a sentence wins.
"""
from jarvis.skills import notes_skills, reminder_skills, memory_skills  # noqa: F401
from jarvis.skills import apps_skills, keys_skills, system_skills, windows_skills  # noqa: F401