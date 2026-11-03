"""Shared limits for models and configuration.

Single source of truth for values that are needed both by the
pydantic models (request validation) and by the API/bot config.
Everything here can be overridden via environment variables.
"""
import os

MAXIMUM_DEBT_CHARACTER_LIMIT: int = int(os.environ.get("MAXIMUM_DEBT_CHARACTER_LIMIT", "200"))
