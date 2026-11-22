from typing import Dict, List

import numpy as np
import pandas as pd
import itertools

from jedi.inference import param

from BayesianNetwork.models.data import Data, DataPurpose


def learn_cpds_em(data: Data, parents: Dict[str, List[str]], max_iter: int=100, tol: float=1e-6,
                   n_restarts:int =5, init: str = "random", seed: int = 0):
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


    # Krok 1: Kodowanie danych (na indeksy)
    # Kodowanie i Dziedziny
    df = data.data_frame
    variables = list(parents.keys())
    var_idx = {v:i for i, v in enumerate(variables)} # kodowanie zmiennej liczbą całkowitą (indeksem)
    n_rows, n  = len(df), len(variables)

    domains = {v: sorted(df[v].dropna().unique().tolist()) for v in variables}
    card = np.array([len(domains[v]) for v in variables]) # Cardinality-liczba stanów danej zmiennej


    # Kodowanie dataframe na liczby całkowite (indeksy) reprezentujące stany zmiennych
    codes = np.full((n_rows, n), -1, dtype=np.int64)
    for v in variables:
        mapping = {val: k for k, val in enumerate(domains[v])}
        codes[:, var_idx[v]] = df[v].map(mapping).fillna(-1).astype(np.int64).values


    # Krok 2: Grupowanie powtarzających się wierszy
    parents, counts = np.unique(codes, return_counts=True)

    return codes