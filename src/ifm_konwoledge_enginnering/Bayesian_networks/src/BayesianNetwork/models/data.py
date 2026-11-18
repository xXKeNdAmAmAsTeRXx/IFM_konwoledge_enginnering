from dataclasses import dataclass
from enum import Enum

import pandas as pd


class DataPurpose(Enum):
    Train = 0
    Test = 1


@dataclass
class Data:
    data_purpose: DataPurpose
    data_frame: pd.DataFrame
