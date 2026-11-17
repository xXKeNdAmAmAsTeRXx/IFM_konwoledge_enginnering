import csv
from typing import List

import pandas as pd

from models.data import Data
from models.variable import Variable


def _validate_header(data_frame: pd.DataFrame) -> None:
    pass


def parse_data(
    path: str,
    variables_dict: dict[str, Variable],
    allow_missing: bool = True,
) -> Data:
   pass
