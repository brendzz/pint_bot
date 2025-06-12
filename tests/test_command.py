from dataclasses import FrozenInstanceError
import pytest
from bot.setup.command import Command


@pytest.fixture(autouse=True)
def clear_registry():
    # Ensure registry is empty before and after each test
    Command._registry.clear()
    yield
    Command._registry.clear()


class TestCommandRegistry:
    def test_basic_registration_and_lookup(self):
        # Register two commands and ensure lookup and all() work
        a = Command(key="a", name="A", description="Desc A", category="Alpha")
        b = Command(key="b", name="B", description="Desc B", category="Beta")

        assert Command.all() == [a, b]
        assert Command.get("a") is a
        assert Command.get("b") is b

    def test_all_returns_copy(self):
        # Mutating returned list from all() does not affect registry
        a = Command(key="a", name="A", description="...", category="Alpha")
        b = Command(key="b", name="B", description="...", category="Beta")

        lst = Command.all()
        assert lst == [a, b]
        lst.pop()
        assert Command.all() == [a, b]

    def test_all_by_category(self):
        a = Command(key="a", name="A", description="...", category="Alpha")
        b = Command(key="b", name="B", description="...", category="Beta")
        c = Command(key="c", name="C", description="...", category="Alpha")

        grouped = Command.all_by_category()
        assert set(grouped.keys()) == {"Alpha", "Beta"}
        assert grouped["Alpha"] == [a, c]
        assert grouped["Beta"] == [b]


class TestCommandLookup:
    def test_missing_key_get_raises(self):
        # Looking up a non-existent key should raise KeyError
        with pytest.raises(KeyError) as exc:
            Command.get("nope")
        assert "No such command: 'nope'" in str(exc.value)


class TestDuplicateKeys:
    def test_duplicate_key_raises(self):
        # Register one command, then attempt duplicate
        Command(key="dup", name="First", description="...", category="X")
        with pytest.raises(ValueError) as exc:
            Command(key="dup", name="Second", description="...", category="X")
        assert "Duplicate command key: 'dup'" in str(exc.value)

    def test_eq_but_duplicate_key_blocked(self):
        # Even if fields match, duplicate key should be blocked
        Command(key="dup", name="D", description="d", category="X")
        with pytest.raises(ValueError):
            Command(key="dup", name="D", description="d", category="X")


class TestImmutability:
    def test_command_is_immutable(self):
        # Command instances should be frozen dataclasses
        cmd = Command(key="x", name="X", description="desc", category="X")
        with pytest.raises(FrozenInstanceError):
            cmd.name = "Y"
