import warnings
from typing import Dict

import pandas as pd

from models.data import Data, DataPurpose
from models.variable import Variable


def _validate_columns(data_frame: pd.DataFrame, variables: Dict[str, Variable]) -> None:
    if sorted(data_frame.columns) != sorted(variables):
        raise Exception("Data do not contain all Variables")


def _validate_states(data_frame: pd.DataFrame, variables: Dict[str, Variable]) -> None:
    for name, variable in variables.items():
        column = data_frame[name].dropna()
        invalid = column[~column.isin(variable.states)]
        if not invalid.empty:
            raise ValueError(
                f"Invalid state {invalid.iloc[0]!r} for variable {name}; "
                f"expected one of {variable.states}"
            )


def _validate_missing(data_frame: pd.DataFrame, purpose: DataPurpose, allow_missing: bool) -> None:
    nans_c = data_frame.isna().sum().sum()
    if nans_c == 0:
        return

    if not allow_missing:
        raise ValueError(f"Data contains {nans_c} nans")

    warnings.warn(f"{purpose.name} data contains {nans_c} nans", UserWarning, stacklevel=3)


def parse_data(
        path: str,
        variables: Dict[str, Variable],
        is_train_data: bool,
        allow_missing: bool = True,
) -> Data:
    data_frame = pd.read_csv(path, dtype=str, keep_default_na=False, na_values=[""])

    _validate_columns(data_frame, variables)
    _validate_states(data_frame, variables)

    purpose = DataPurpose.Train if is_train_data else DataPurpose.Test
    _validate_missing(data_frame, purpose, allow_missing)

    return Data(
        data_purpose=purpose,
        data_frame=data_frame,
    )
