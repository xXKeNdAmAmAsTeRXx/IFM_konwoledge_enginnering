import csv
from pathlib import Path

import pytest

from models.data import DataPurpose
from parsing.data_parsing import parse_data
from parsing.description_parsing import description_parser


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ZESTAWY = PROJECT_ROOT / "data" / "zestawy"
DATASETS = sorted(path for path in ZESTAWY.iterdir() if path.is_dir())


def _csv_row_count(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.reader(f)) - 1


def _variables(dataset):
    return description_parser(str(dataset / "opis.json")).variables_dict


@pytest.mark.parametrize("dataset", DATASETS, ids=[path.name for path in DATASETS])
def test_training_file_parses_with_all_rows(dataset):
    variables = _variables(dataset)

    data = parse_data(str(dataset / "dane.csv"), variables, is_train_data=True)

    assert data.data_purpose == DataPurpose.Train
    assert len(data.data_frame) == _csv_row_count(dataset / "dane.csv")
    assert set(data.data_frame.columns) == set(variables)


@pytest.mark.parametrize("dataset", DATASETS, ids=[path.name for path in DATASETS])
def test_test_file_parses_without_missing_values(dataset):
    variables = _variables(dataset)

    data = parse_data(
        str(dataset / "test.csv"), variables, is_train_data=False, allow_missing=False
    )

    assert data.data_purpose == DataPurpose.Test
    assert len(data.data_frame) == _csv_row_count(dataset / "test.csv")
    assert data.data_frame.isna().sum().sum() == 0
