import csv
from typing import List

import pandas as pd

from models.data import Data, DataPurpose
from models.variable import Variable


def _validate_data(data_frame: pd.DataFrame, purpose: DataPurpose, variable_names: List[str],
                   allow_missing: bool) -> None:
    nans_c = data_frame.isna().sum().sum()

    columns = data_frame.columns
    if sorted(columns) != sorted(variable_names):
        raise Exception("Data do not contain all Variables")

    if nans_c > 0:
        if allow_missing:
            print(f"Warning: Train data contains {nans_c} nans")
        else:
            raise ValueError(f"Data contains {nans_c} nans")
    else:
        print("Data contains all Variables (No NaNs)")

def parse_data(
        path: str,
        variable_names: List[str],
        is_train_data: bool,
        allow_missing: bool = True,
) -> Data:
    data_frame = pd.read_csv(path)

    _validate_data(data_frame)

    return Data(
        data_purpose=DataPurpose.Train if is_train_data else DataPurpose.Test,
        data_frame=data_frame
    )
