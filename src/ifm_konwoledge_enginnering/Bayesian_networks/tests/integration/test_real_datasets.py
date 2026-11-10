from pathlib import Path

import pytest

from models.graph import GraphData
from parsing.description_parsing import description_parser
from parsing.query_parsing import query_parser


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRZYKLAD = PROJECT_ROOT / "przyklad"
K24 = PROJECT_ROOT / "data" / "zestawy" / "k24"


@pytest.mark.parametrize(
    "description_path, expert_count, required_count, forbidden_count, tier_sizes",
    [
        (PRZYKLAD / "opis.json", 4, 4, 2, [2, 2, 1]),
        (K24 / "opis.json", 7, 4, 4, [4, 1, 2, 1, 1]),
    ],
    ids=["przyklad", "k24"],
)
def test_description_parser_real_dataset(
    description_path, expert_count, required_count, forbidden_count, tier_sizes
):
    graph = description_parser(str(description_path))

    assert isinstance(graph, GraphData)
    assert len(graph.exper_edges) == expert_count
    assert len(graph.required_edges) == required_count
    assert len(graph.forbidden_edges) == forbidden_count
    assert [len(tier) for tier in graph.tiers] == tier_sizes


def test_description_parser_przyklad_variable_names():
    graph = description_parser(str(PRZYKLAD / "opis.json"))

    assert [(left.name, right.name) for left, right in graph.exper_edges] == [
        ("D", "G"),
        ("I", "G"),
        ("G", "L"),
        ("I", "S"),
    ]
    assert [[variable.name for variable in tier] for tier in graph.tiers] == [
        ["D", "I"],
        ["G", "S"],
        ["L"],
    ]


@pytest.mark.parametrize(
    "query_path, expected_count",
    [
        (PRZYKLAD / "zapytania.txt", 8),
        (K24 / "zapytania.txt", 19),
    ],
    ids=["przyklad", "k24"],
)
def test_query_parser_real_dataset(query_path, expected_count, extended_student_variables):
    queries = query_parser(str(query_path), extended_student_variables)

    assert len(queries) == expected_count


def test_query_parser_przyklad_query_order(extended_student_variables):
    queries = query_parser(str(PRZYKLAD / "zapytania.txt"), extended_student_variables)

    assert [query.variables[0].name for query in queries] == [
        "G",
        "G",
        "I",
        "I",
        "I",
        "G",
        "G",
        "D",
    ]
    assert [len(query.variables) for query in queries] == [1, 1, 1, 1, 1, 2, 1, 2]
