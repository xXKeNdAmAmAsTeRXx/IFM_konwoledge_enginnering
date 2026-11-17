import csv
from typing import List

import pandas as pd

from models.data import Data, DataPurpose
from models.variable import Variable


def _validate_data(data_frame: pd.DataFrame, purpose: DataPurpose, variable_names: List[str]) -> None:
    nans_c = data_frame.isna().sum().sum()

    columns = data_frame.columns
    if sorted(columns) != sorted(variable_names):
        raise Exception("Data do not contain all Variables")

    if nans_c > 0:
        if purpose == DataPurpose.Test:
            raise ValueError(f"Test data contains {nans_c}nans")

        if purpose == DataPurpose.Train:
            print(f"Warning: Train data contains {nans_c} nans")
    else:
        print("Data contains all Variables (No NaNs)")

    pass

def parse_data(
    path: str,
    variable_names: List[str],
    allow_missing: bool = True,
) -> Data:

    #TODO: Count Rows

    #TODO: Parse Enum

    #TODO: Load CSV to DF

    pass
