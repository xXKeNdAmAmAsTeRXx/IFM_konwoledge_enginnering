import pytest
from package_manager.model import State
from package_manager.state import parse_state
from packaging.version import Version

# Test State Parsing

def test_parse_state_empty():
    assert parse_state("") == State()

def test_parse_state_single():
    state = parse_state("lib 1.0")
    assert state.packages == {"lib": (Version("1.0"), False)}

def test_parse_state_manual():
    state = parse_state("app 2.0 manual")
    assert state.packages == {"app": (Version("2.0"), True)}

def test_parse_state_comments():
    state = parse_state("lib 1.0 # comment\napp 2.0 manual")
    assert "lib" in state.packages
    assert "app" in state.packages