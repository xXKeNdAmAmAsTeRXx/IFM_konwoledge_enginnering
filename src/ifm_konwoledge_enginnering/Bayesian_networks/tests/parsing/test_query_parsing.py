import pytest

from models.queries import Query, QueryType
from parsing.query_parsing import parse_query, query_parser


def _names(variables):
    return [variable.name for variable in variables]


@pytest.mark.parametrize(
    "line, query_type, target_names, expected_evidence",
    [
        ("P(G)", QueryType.P, ["G"], {}),
        ("P(G, L)", QueryType.P, ["G", "L"], {}),
        ("P(G | S==Good)", QueryType.P, ["G"], {"S": "Good"}),
        (
            "P(G, L | S==Good, D==Easy)",
            QueryType.P,
            ["G", "L"],
            {"S": "Good", "D": "Easy"},
        ),
        ("MAP(G)", QueryType.MAP, ["G"], {}),
        (
            "MAP(G | D==Easy, I==Intelligent)",
            QueryType.MAP,
            ["G"],
            {"D": "Easy", "I": "Intelligent"},
        ),
        (
            "MAP(I, D | G==A, S==Good)",
            QueryType.MAP,
            ["I", "D"],
            {"G": "A", "S": "Good"},
        ),
    ],
)
def test_parse_query_valid(
    line, query_type, target_names, expected_evidence, student_variables
):
    query = parse_query(line, student_variables)

    assert isinstance(query, Query)
    assert query.query_type == query_type
    assert _names(query.variables) == target_names
    assert query.evidence == expected_evidence


def test_query_types_are_distinct():
    assert QueryType.P is not QueryType.MAP


def test_parse_query_tolerates_whitespace(student_variables):
    query = parse_query(
        "  P( G , L | S == Good , D == Easy )  ",
        student_variables,
    )

    assert _names(query.variables) == ["G", "L"]
    assert query.evidence == {"S": "Good", "D": "Easy"}


def test_parse_query_without_evidence_returns_empty_dict(student_variables):
    query = parse_query("P(G)", student_variables)

    assert query.evidence == {}


def test_parse_query_evidence_uses_validated_names_and_states(student_variables):
    query = parse_query("P(G | S==Good, D==Easy)", student_variables)

    assert query.variables == [student_variables["G"]]
    assert query.evidence == {"S": "Good", "D": "Easy"}
    assert set(query.evidence).issubset(student_variables)
    assert {variable.name for variable in query.variables}.isdisjoint(query.evidence)


def test_query_parser_preserves_evidence_assignments(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("P(G | S==Good, D==Easy)\n", encoding="utf-8")

    query = query_parser(str(path), student_variables)[0]

    assert query.evidence == {"S": "Good", "D": "Easy"}


@pytest.mark.parametrize(
    "line",
    [
        "Q(G)",
        "p(G)",
        "P G",
        "P(G",
        "P(G))",
        "P()",
        "P(G | S==Good | D==Easy)",
        "P(G | S Good)",
        "P(G | )",
        "P(G | S==Good, )",
    ],
)
def test_parse_query_rejects_malformed_input(line, student_variables):
    with pytest.raises(ValueError):
        parse_query(line, student_variables)


@pytest.mark.parametrize(
    "line, expected_text",
    [
        ("P(Z)", "Z"),
        ("P(G | Z==Good)", "Z"),
        ("P(G | S==Excellent)", "Excellent"),
    ],
)
def test_parse_query_rejects_unknown_variable_or_state(
    line, expected_text, student_variables
):
    with pytest.raises(ValueError, match=expected_text):
        parse_query(line, student_variables)


def test_parse_query_rejects_target_variable_in_evidence(student_variables):
    with pytest.raises(ValueError, match="G"):
        parse_query("P(G | G==A)", student_variables)


# query_parser


def test_query_parser_empty_file(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("", encoding="utf-8")

    assert query_parser(str(path), student_variables) == []


def test_query_parser_only_blank_lines(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("\n\n\n", encoding="utf-8")

    assert query_parser(str(path), student_variables) == []


def test_query_parser_only_whitespace_lines(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("   \n\t\n  \n", encoding="utf-8")

    assert query_parser(str(path), student_variables) == []


def test_query_parser_only_comments(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("# first comment\n# second comment\n", encoding="utf-8")

    assert query_parser(str(path), student_variables) == []


def test_query_parser_skips_comments_with_leading_whitespace(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("   # indented comment\n", encoding="utf-8")

    assert query_parser(str(path), student_variables) == []


def test_query_parser_strips_inline_comments(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("P(G)  # query without evidence\n", encoding="utf-8")

    queries = query_parser(str(path), student_variables)

    assert len(queries) == 1
    assert _names(queries[0].variables) == ["G"]
    assert queries[0].evidence == {}


def test_query_parser_preserves_order(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("P(G)\nP(L)\nMAP(G | D==Easy)\n", encoding="utf-8")

    queries = query_parser(str(path), student_variables)

    assert [_names(query.variables) for query in queries] == [["G"], ["L"], ["G"]]
    assert [query.query_type for query in queries] == [
        QueryType.P,
        QueryType.P,
        QueryType.MAP,
    ]


def test_query_parser_returns_query_instances(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("P(G)\n", encoding="utf-8")

    queries = query_parser(str(path), student_variables)

    assert all(isinstance(query, Query) for query in queries)


def test_query_parser_validates_variables(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("P(Z)\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Z"):
        query_parser(str(path), student_variables)


def test_query_parser_error_contains_line_number(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("# header\nP(G)\nQ(H)\n", encoding="utf-8")

    with pytest.raises(ValueError) as error:
        query_parser(str(path), student_variables)

    assert "3" in str(error.value)


def test_query_parser_handles_crlf(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("P(G)\r\nP(L)\r\n", encoding="utf-8")

    queries = query_parser(str(path), student_variables)

    assert len(queries) == 2
    assert [_names(query.variables) for query in queries] == [["G"], ["L"]]


def test_query_parser_handles_missing_final_newline(tmp_path, student_variables):
    path = tmp_path / "zapytania.txt"
    path.write_text("P(G)", encoding="utf-8")

    queries = query_parser(str(path), student_variables)

    assert len(queries) == 1
    assert _names(queries[0].variables) == ["G"]


def test_query_parser_missing_file(tmp_path, student_variables):
    with pytest.raises(FileNotFoundError):
        query_parser(str(tmp_path / "does_not_exist.txt"), student_variables)
