from pathlib import Path

import pytest

from models.data import Data, Observation
from models.variable import Variable
from parsing.data_parsing import parse_data


def _write_csv(tmp_path, content, name="data.csv"):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(path)


# Happy path


def test_parse_data_returns_data_model(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\na0,b0,c0\na1,b1,c1\n")

    data = parse_data(path, variables_dict)

    assert isinstance(data, Data)
    assert len(data.observations) == 2
    assert all(isinstance(observation, Observation) for observation in data.observations)


def test_parse_data_parses_complete_rows(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\na0,b0,c0\na1,b1,c1\n")

    data = parse_data(path, variables_dict)

    assert data.observations == [
        Observation(states={"A": "a0", "B": "b0", "C": "c0"}),
        Observation(states={"A": "a1", "B": "b1", "C": "c1"}),
    ]


def test_parse_data_header_order_is_irrelevant(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "C,A,B\nc1,a0,b1\n")

    data = parse_data(path, variables_dict)

    assert data.observations[0].states == {"C": "c1", "A": "a0", "B": "b1"}


def test_parse_data_preserves_row_count_and_order(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\na1,b0,c0\na0,b1,c1\na1,b1,c0\n")

    data = parse_data(path, variables_dict)

    assert len(data.observations) == 3
    assert data.observations[0].states == {"A": "a1", "B": "b0", "C": "c0"}
    assert data.observations[-1].states == {"A": "a1", "B": "b1", "C": "c0"}


def test_parse_data_header_only_returns_no_observations(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\n")

    data = parse_data(path, variables_dict)

    assert data.observations == []


# Missing values


def test_parse_data_maps_empty_field_to_none(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\na0,,c0\n")

    data = parse_data(path, variables_dict)

    assert data.observations[0].states == {"A": "a0", "B": None, "C": "c0"}


def test_parse_data_keeps_missing_columns_in_observation(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\n,,c0\n")

    observation = parse_data(path, variables_dict).observations[0]

    assert set(observation.states) == set(variables_dict)
    assert observation.states == {"A": None, "B": None, "C": "c0"}


def test_parse_data_does_not_validate_none_as_state(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\n,,c0\n")

    data = parse_data(path, variables_dict)

    assert data.observations[0].states["A"] is None


def test_parse_data_allows_missing_values_by_default(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\na0,,\n")

    data = parse_data(path, variables_dict)

    assert data.observations[0].states == {"A": "a0", "B": None, "C": None}


def test_parse_data_rejects_missing_values_when_disallowed(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\na0,b0,\n")

    with pytest.raises(ValueError, match="C"):
        parse_data(path, variables_dict, allow_missing=False)


def test_parse_data_trims_whitespace(tmp_path, variables_dict):
    path = _write_csv(tmp_path, " A , B , C \n a0 , b0 , c0 \n")

    data = parse_data(path, variables_dict)

    assert data.observations[0].states == {"A": "a0", "B": "b0", "C": "c0"}


def test_parse_data_treats_whitespace_only_field_as_missing(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\na0,   ,c0\n")

    data = parse_data(path, variables_dict)

    assert data.observations[0].states == {"A": "a0", "B": None, "C": "c0"}


# State validation


def test_parse_data_rejects_unknown_state(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\nunknown,b0,c0\n")

    with pytest.raises(ValueError, match="unknown"):
        parse_data(path, variables_dict)


def test_parse_data_propagates_error_with_variable_name(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\na0,not_a_state,c0\n")

    with pytest.raises(ValueError, match="B"):
        parse_data(path, variables_dict)


def test_parse_data_accepts_state_from_correct_variable(tmp_path):
    variables = {
        "A": Variable(name="A", description="a", states=["shared"]),
        "B": Variable(name="B", description="b", states=["other"]),
    }
    path = _write_csv(tmp_path, "A,B\nshared,other\n")

    data = parse_data(path, variables)

    assert data.observations[0].states == {"A": "shared", "B": "other"}


# CSV structure errors


def test_parse_data_rejects_unknown_column(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,Z\na0,b0,c0\n")

    with pytest.raises(ValueError, match="Z"):
        parse_data(path, variables_dict)


def test_parse_data_rejects_missing_column(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B\na0,b0\n")

    with pytest.raises(ValueError, match="C"):
        parse_data(path, variables_dict)


def test_parse_data_rejects_duplicate_column(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C,C\na0,b0,c0,c0\n")

    with pytest.raises(ValueError, match="duplicate"):
        parse_data(path, variables_dict)


def test_parse_data_rejects_too_few_fields(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\na0,b0\n")

    with pytest.raises(ValueError, match="expected 3"):
        parse_data(path, variables_dict)


def test_parse_data_rejects_too_many_fields(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\na0,b0,c0,extra\n")

    with pytest.raises(ValueError, match="expected 3"):
        parse_data(path, variables_dict)


def test_parse_data_rejects_blank_line(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\na0,b0,c0\n\n")

    with pytest.raises(ValueError, match="blank line"):
        parse_data(path, variables_dict)


def test_parse_data_rejects_blank_header_name(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,,C\na0,b0,c0\n")

    with pytest.raises(ValueError, match="empty column name"):
        parse_data(path, variables_dict)


def test_parse_data_rejects_empty_file(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "")

    with pytest.raises(ValueError, match="header"):
        parse_data(path, variables_dict)


def test_parse_data_missing_file(tmp_path, variables_dict):
    missing = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        parse_data(str(missing), variables_dict)


# Error context


def test_parse_data_error_contains_line_number(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\nunknown,b0,c0\n")

    with pytest.raises(ValueError) as error:
        parse_data(path, variables_dict)

    assert ":2:" in str(error.value)


def test_parse_data_error_contains_path(tmp_path, variables_dict):
    path = _write_csv(tmp_path, "A,B,C\nunknown,b0,c0\n")

    with pytest.raises(ValueError) as error:
        parse_data(path, variables_dict)

    assert path in str(error.value)
