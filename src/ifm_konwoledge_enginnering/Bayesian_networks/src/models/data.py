from dataclasses import dataclass

import pandas as pd
from traitlets import Enum

class DataPurpose(Enum):
    Train = 0,
    Test = 1

@dataclass
class Data:
     data_purpose: DataPurpose
     DataFrame: pd.DataFrame