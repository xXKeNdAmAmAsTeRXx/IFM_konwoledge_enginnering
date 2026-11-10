import os
import sys

import pytest

SRC = os.path.join(os.path.dirname(__file__), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from models.variable import Variable  # noqa: E402


@pytest.fixture
def variables_dict():
    return {
        "A": Variable(name="A", description="variable A", states=["a0", "a1"]),
        "B": Variable(name="B", description="variable B", states=["b0", "b1"]),
        "C": Variable(name="C", description="variable C", states=["c0", "c1"]),
    }


@pytest.fixture
def student_variables():
    return {
        "D": Variable(name="D", description="course difficulty", states=["Easy", "Hard"]),
        "I": Variable(name="I", description="student intelligence", states=["Dumb", "Intelligent"]),
        "G": Variable(name="G", description="course grade", states=["A", "B", "C"]),
        "S": Variable(name="S", description="SAT score", states=["Bad", "Good"]),
        "L": Variable(name="L", description="recommendation letter", states=["Bad", "Good"]),
    }


@pytest.fixture
def extended_student_variables():
    return {
        "D": Variable(name="D", description="course difficulty", states=["Easy", "Hard"]),
        "I": Variable(name="I", description="student intelligence", states=["Dumb", "Intelligent"]),
        "W": Variable(name="W", description="part-time work", states=["No", "Yes"]),
        "Q": Variable(name="Q", description="lecturer quality", states=["Low", "High"]),
        "E": Variable(name="E", description="preparatory course", states=["No", "Yes"]),
        "G": Variable(name="G", description="course grade", states=["A", "B", "C"]),
        "S": Variable(name="S", description="SAT score", states=["Bad", "Good"]),
        "L": Variable(name="L", description="recommendation letter", states=["Bad", "Good"]),
        "R": Variable(name="R", description="admission result", states=["Rejected", "Waitlisted", "Admitted"]),
    }


@pytest.fixture
def valid_description_payload():
    return {
        "meta": {"description": "valid test description"},
        "variables": {
            "A": {"description": "variable A", "states": ["a0", "a1"]},
            "B": {"description": "variable B", "states": ["b0", "b1"]},
            "C": {"description": "variable C", "states": ["c0", "c1"]},
        },
        "expert_edges": [["A", "B"], ["B", "C"]],
        "required_edges": [["A", "B"]],
        "forbidden_edges": [["C", "A"]],
        "tiers": [["A"], ["B"], ["C"]],
    }
