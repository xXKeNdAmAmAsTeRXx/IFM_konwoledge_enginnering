import pytest

from BayesianNetwork.models.data import DataPurpose
from BayesianNetwork.parsing.data_parsing import parse_data
from BayesianNetwork.parsing.description_parsing import description_parser


@pytest.mark.parametrize(
    "filename, is_train_data, expected_purpose, expected_rows",
    [
        ("dane.csv", True, DataPurpose.Train, 5),
        ("test.csv", False, DataPurpose.Test, 3),
    ],
    ids=["training-data", "test-data"],
)
def test_dataset_file_parses_with_expected_rows(
    integration_dataset, filename, is_train_data, expected_purpose, expected_rows
):
    variables = description_parser(str(integration_dataset / "opis.json")).variables_dict

    data = parse_data(
        str(integration_dataset / filename),
        variables,
        is_train_data=is_train_data,
        allow_missing=is_train_data,
    )

    assert data.data_purpose == expected_purpose
    assert len(data.data_frame) == expected_rows
    assert set(data.data_frame.columns) == set(variables)
    if not is_train_data:
        assert data.data_frame.isna().sum().sum() == 0
