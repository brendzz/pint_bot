"""Module for defining the command dataclass."""
from collections import defaultdict
from dataclasses import dataclass
from typing import ClassVar

@dataclass(frozen=True)
class Command:
    """
    Represents a command with its key, name, and description.
    Attributes:
        key (str): The unique key for the command.
        name (str): The name of the command.
        description (str): A brief description of the command.
        category (str): The category to which the command belongs.
    """
    key: str
    name: str
    description: str
    category: str

    _registry: ClassVar[dict[str, "Command"]] = {}

    def __post_init__(self):
        cls = self.__class__
        if self.key in cls._registry:
            raise ValueError(f"Duplicate command key: {self.key!r}")
        cls._registry[self.key] = self

    @classmethod
    def get(cls, key: str) -> "Command":
        """Retrieves a command by its key."""
        try:
            return cls._registry[key]
        except KeyError:
            raise KeyError(f"No such command: {key!r}")

    @classmethod
    def all(cls) -> list["Command"]:
        """Returns a list of all registered commands in the order they were added."""
        # returns in insertion order
        return list(cls._registry.values())
    
    @classmethod
    def all_by_category(cls) -> dict[str, list["Command"]]:
        """Returns all commands grouped by their category."""
        groups = defaultdict(list)
        for command in cls._registry.values():
            groups[command.category].append(command)
        return dict(groups)
