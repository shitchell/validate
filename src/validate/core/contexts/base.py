"""
Base ValidationContext and common context models.
"""

from pydantic import BaseModel, ConfigDict
from pathlib import Path
from argparse import Namespace
from abc import ABC
from typing import Any


class ValidationContext(BaseModel, ABC):
    """
    Base validation context.

    All contexts share these minimal fields.
    Domain-specific contexts should subclass this.

    Attributes:
        target: What's being validated (file path, URL, etc.)
        args: Parsed command-line arguments
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    target: Path | str
    args: Namespace
