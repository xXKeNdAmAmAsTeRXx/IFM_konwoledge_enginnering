import pytest
from package_manager.model import State
from package_manager.state import parse_state, write_state
from packaging.version import Version


def test_state_get_packages_list_empy():
    state = State()
    assert state.get_packages_list() == []
def test_state_get_packages_list():
    state = State(packages={"lib": (Version("1.0"), False)})
    assert state.get_packages_list() == [("lib", "1.0")]

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

# Write State
def test_state_to_text_empty():
    assert write_state(State()) == ""

def test_state_to_text_single():
    state = State(packages={"lib": (Version("1.0"), False)})
    assert write_state(state) == "lib 1.0\n"

def test_state_to_text_manual():
    state = State(packages={"app": (Version("2.0"), True)})
    assert write_state(state) == "app 2.0 manual\n"

def test_state_round_trip():
    text = "lib 1.0\napp 2.0 manual\n"
    assert write_state(parse_state(text)) == text