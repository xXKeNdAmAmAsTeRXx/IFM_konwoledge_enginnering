from typing import Dict, List

import numpy as np
import pandas as pd
import itertools

from jedi.inference import param

from BayesianNetwork.models.data import Data, DataPurpose


def learn_cpds_em(data: Data, parents: Dict[str, List[str]], max_iter: int=100, tol: float=1e-6):
    """
    Uczy tablice CPD z danych z brakami za pomocą algorytmu EM.

    Parametry:
    - data: obiekt data z danymi do estymacji cdp
    - parents: słownik mapujący każdą zmienną na listę jej rodziców, np. {'A': [], 'B': ['A']}
    - max_iter: maksymalna liczba iteracji
    - tol: próg zbieżności
    """

    if data.data_purpose == DataPurpose.Test:
        raise Exception("Training or Estimation should not be performed on test data")


    df = data.data_frame
    # Wyznaczenie dziedziny dla każdej zmiennej

    # Inicjalizacja CDP


    for iter in range(max_iter):
        # E-krok: Oczekiwane zliczenia i log-wiarygodności

        pass

        # M-krok: Częstości z oczekiwanych zliczeń



    pass