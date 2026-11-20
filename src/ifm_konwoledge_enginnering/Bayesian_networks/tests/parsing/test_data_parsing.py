import warnings

import pandas as pd
import pytest

from BayesianNetwork.models.data import Data, DataPurpose
from BayesianNetwork.models.variable import Variable
from BayesianNetwork.parsing.data_parsing import parse_data


# Happy path


def test_parse_data_returns_data_model(write_csv, variables_dict):
    path = write_csv("A,B,C\na0,b0,c0\na1,b1,c1\n")

    data = parse_data(path, variables_dict, is_train_data=True)

    assert isinstance(data, Data)
    assert isinstance(data.data_frame, pd.DataFrame)


def test_parse_data_train_flag_sets_train_purpose(write_csv, variables_dict):
    path = write_csv("A,B,C\na0,b0,c0\n")

    data = parse_data(path, variables_dict, is_train_data=True)

    assert data.data_purpose == DataPurpose.Train


def test_parse_data_test_flag_sets_test_purpose(write_csv, variables_dict):
    path = write_csv("A,B,C\na0,b0,c0\n")

    data = parse_data(path, variables_dict, is_train_data=False)

    assert data.data_purpose == DataPurpose.Test


def test_parse_data_preserves_values_and_row_order(write_csv, variables_dict):
    path = write_csv("A,B,C\na1,b0,c0\na0,b1,c1\na1,b1,c0\n")

    data = parse_data(path, variables_dict, is_train_data=True)

    assert data.data_frame.values.tolist() == [
        ["a1", "b0", "c0"],
        ["a0", "b1", "c1"],
        ["a1", "b1", "c0"],
    ]


def test_parse_data_columns_match_variable_names(write_csv, variables_dict):
    path = write_csv("C,A,B\nc1,a0,b1\n")

    data = parse_data(path, variables_dict, is_train_data=True)

    assert set(data.data_frame.columns) == set(variables_dict)
    assert data.data_frame["A"].tolist() == ["a0"]
    assert data.data_frame["C"].tolist() == ["c1"]


def test_parse_data_header_only_returns_empty_frame(write_csv, variables_dict):
    path = write_csv("A,B,C\n")

    data = parse_data(path, variables_dict, is_train_data=True)

    assert len(data.data_frame) == 0
    assert set(data.data_frame.columns) == set(variables_dict)


# Missing values


def test_parse_data_maps_empty_field_to_nan(write_csv, variables_dict):
    path = write_csv("A,B,C\na0,,c0\n")

    data = parse_data(path, variables_dict, is_train_data=True)

    assert pd.isna(data.data_frame.loc[0, "B"])
    assert data.data_frame.loc[0, "A"] == "a0"
    assert data.data_frame.loc[0, "C"] == "c0"


def test_parse_data_warns_on_missing_train_values_by_default(write_csv, variables_dict):
    path = write_csv("A,B,C\na0,b0,\n")

    with pytest.warns(UserWarning, match="Train data contains 1 nans"):
        parse_data(path, variables_dict, is_train_data=True)


def test_parse_data_warns_on_missing_test_values_when_allowed(write_csv, variables_dict):
    path = write_csv("A,B,C\na0,b0,\n")

    with pytest.warns(UserWarning, match="Test data contains 1 nans"):
        parse_data(path, variables_dict, is_train_data=False, allow_missing=True)


def test_parse_data_rejects_missing_values_when_disallowed(write_csv, variables_dict):
    path = write_csv("A,B,C\na0,b0,\n")

    with pytest.raises(ValueError, match="Data contains 1 nans"):
        parse_data(path, variables_dict, is_train_data=True, allow_missing=False)


def test_parse_data_rejects_missing_test_values_when_disallowed(write_csv, variables_dict):
    path = write_csv("A,B,C\na0,b0,\n")

    with pytest.raises(ValueError, match="Data contains 1 nans"):
        parse_data(path, variables_dict, is_train_data=False, allow_missing=False)


def test_parse_data_counts_all_missing_cells_when_disallowed(write_csv, variables_dict):
    path = write_csv("A,B,C\na0,,\n,,\n")

    with pytest.raises(ValueError, match="Data contains 5 nans"):
        parse_data(path, variables_dict, is_train_data=True, allow_missing=False)


def test_parse_data_does_not_warn_when_complete(write_csv, variables_dict):
    path = write_csv("A,B,C\na0,b0,c0\n")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        parse_data(path, variables_dict, is_train_data=True)


# State validation


def test_parse_data_accepts_declared_states(write_csv, variables_dict):
    path = write_csv("A,B,C\na1,b1,c1\n")

    data = parse_data(path, variables_dict, is_train_data=True)

    assert data.data_frame.values.tolist() == [["a1", "b1", "c1"]]


def test_parse_data_accepts_state_from_correct_variable(write_csv):
    variables = {
        "A": Variable(name="A", description="a", states=["shared"]),
        "B": Variable(name="B", description="b", states=["other"]),
    }
    path = write_csv("A,B\nshared,other\n")

    data = parse_data(path, variables, is_train_data=True)

    assert data.data_frame.values.tolist() == [["shared", "other"]]


def test_parse_data_rejects_unknown_state(write_csv, variables_dict):
    path = write_csv("A,B,C\nunknown,b0,c0\n")

    with pytest.raises(ValueError, match="Invalid state 'unknown' for variable A"):
        parse_data(path, variables_dict, is_train_data=True)


def test_parse_data_rejects_state_from_other_variable(write_csv):
    variables = {
        "A": Variable(name="A", description="a", states=["a0", "a1"]),
        "B": Variable(name="B", description="b", states=["b0", "b1"]),
    }
    path = write_csv("A,B\nb0,a0\n")

    with pytest.raises(ValueError, match="for variable A"):
        parse_data(path, variables, is_train_data=True)


def test_parse_data_state_match_is_case_sensitive(write_csv, variables_dict):
    path = write_csv("A,B,C\nA0,b0,c0\n")

    with pytest.raises(ValueError, match="'A0'"):
        parse_data(path, variables_dict, is_train_data=True)


def test_parse_data_does_not_trim_whitespace_in_states(write_csv, variables_dict):
    path = write_csv("A,B,C\n a0,b0,c0\n")

    with pytest.raises(ValueError, match="' a0'"):
        parse_data(path, variables_dict, is_train_data=True)


def test_parse_data_rejects_invalid_state_in_later_row(write_csv, variables_dict):
    path = write_csv("A,B,C\na0,b0,c0\na1,b1,c1\na0,b0,bad\n")

    with pytest.raises(ValueError, match="'bad' for variable C"):
        parse_data(path, variables_dict, is_train_data=True)


def test_parse_data_keeps_declared_na_like_states_as_values(write_csv):
    variables = {
        "A": Variable(name="A", description="a", states=["NA", "None", "null"]),
    }
    path = write_csv("A\nNA\nNone\nnull\n")

    data = parse_data(path, variables, is_train_data=True)

    assert data.data_frame["A"].tolist() == ["NA", "None", "null"]
    assert data.data_frame.isna().sum().sum() == 0


def test_parse_data_keeps_numeric_looking_states_as_strings(write_csv):
    variables = {
        "A": Variable(name="A", description="a", states=["0", "01", "1.0"]),
    }
    path = write_csv("A\n0\n01\n1.0\n")

    data = parse_data(path, variables, is_train_data=True)

    assert data.data_frame["A"].tolist() == ["0", "01", "1.0"]


def test_parse_data_skips_state_check_for_missing_values(write_csv, variables_dict):
    path = write_csv("A,B,C\na0,,c0\n")

    data = parse_data(path, variables_dict, is_train_data=True)

    assert pd.isna(data.data_frame.loc[0, "B"])


# Column validation


def test_parse_data_rejects_extra_column(write_csv, variables_dict):
    path = write_csv("A,B,Z\na0,b0,c0\n")

    with pytest.raises(Exception, match="Data do not contain all Variables"):
        parse_data(path, variables_dict, is_train_data=True)


def test_parse_data_rejects_missing_column(write_csv, variables_dict):
    path = write_csv("A,B\na0,b0\n")

    with pytest.raises(Exception, match="Data do not contain all Variables"):
        parse_data(path, variables_dict, is_train_data=True)


def test_parse_data_rejects_duplicate_column(write_csv, variables_dict):
    path = write_csv("A,B,C,C\na0,b0,c0,c0\n")

    with pytest.raises(Exception, match="Data do not contain all Variables"):
        parse_data(path, variables_dict, is_train_data=True)


# File errors


def test_parse_data_missing_file(tmp_path, variables_dict):
    missing = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        parse_data(str(missing), variables_dict, is_train_data=True)
