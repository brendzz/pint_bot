from dataclasses import dataclass
from typing import ClassVar

@dataclass(frozen=True)
class Command:
    key: str
    name: str
    description: str

    _registry: ClassVar[dict[str, "Command"]] = {}

    def __post_init__(self):
        cls = self.__class__
        if self.key in cls._registry:
            raise ValueError(f"Duplicate command key: {self.key!r}")
        cls._registry[self.key] = self

    @classmethod
    def get(cls, key: str) -> "Command":
        try:
            return cls._registry[key]
        except KeyError:
            raise KeyError(f"No such command: {key!r}")

    @classmethod
    def all(cls) -> list["Command"]:
        # returns in insertion order
        return list(cls._registry.values())
