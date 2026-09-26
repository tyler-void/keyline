"""What keyline is working on right now, for the one-line internal-error message (A-17)."""

from contextvars import ContextVar

reading: ContextVar[str] = ContextVar("keyline_reading", default="the deck")
