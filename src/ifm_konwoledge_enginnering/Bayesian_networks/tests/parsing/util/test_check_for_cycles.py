import copy

import pytest

from parsing.util.check_for_cycles import check_for_cycles


@pytest.mark.parametrize(
    "edges, expected",
    [
        ([], False),
        ([("A", "B")], False),
        ([("A", "B"), ("B", "C"), ("C", "D")], False),
        ([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D")], False),
        ([("A", "B"), ("C", "D")], False),
        ([("A", "A")], True),
        ([("A", "B"), ("B", "A")], True),
        ([("A", "B"), ("B", "C"), ("C", "A")], True),
        ([("A", "B"), ("B", "C"), ("C", "B")], True),
        ([("A", "B"), ("C", "D"), ("D", "E"), ("E", "C")], True),
        ([("A", "B"), ("C", "D")], False),
        ([("A", "B"), ("A", "B")], False),
        ([("A", "B"), ("B", "C"), ("C", "D")], False),
    ],
)
def test_check_for_cycles(edges, expected):
    assert check_for_cycles(edges) is expected


def test_check_for_cycles_destination_only_node():
    assert check_for_cycles([("A", "B"), ("C", "B")]) is False


def test_check_for_cycles_accepts_list_of_lists():
    assert check_for_cycles([["A", "B"], ["B", "C"]]) is False
    assert check_for_cycles([["A", "B"], ["B", "A"]]) is True


def test_check_for_cycles_is_independent_of_edge_order():
    edges = [("A", "B"), ("B", "C"), ("C", "D")]
    reversed_edges = list(reversed(edges))

    assert check_for_cycles(edges) == check_for_cycles(reversed_edges)


def test_check_for_cycles_does_not_mutate_edges():
    edges = [["A", "B"], ["B", "C"]]
    original = copy.deepcopy(edges)

    check_for_cycles(edges)

    assert edges == original
