import warnings
from typing import Dict, List
import numpy as np
import pandas as pd
from pgmpy.factors.discrete import TabularCPD

from BayesianNetwork.models.data import Data, DataPurpose


# KROK 4: Inicjalizacja CPD

def _random_cdp(shape, rng):
    """Tworzy losową CPD i normalizuje jej wiersze."""
    g = rng.gamma(1.0, size=shape)
    return g / g.sum(axis=-1, keepdims=True)

def _count_init(scopes, card, codes):
    """Inicjalizuje CPD zliczeniami z kompletnych wierszy."""

    full = codes[(codes >= 0).all(axis=1)]
    cdps = []
    for s in scopes:
        C = np.ones(card[s])
        np.add.at(C, tuple(full[:, s].T), 1)
        cdps.append(C / C.sum(axis=-1, keepdims=True))

    return cdps

# KROK 5: Budowa rozkładu łącznego
def _build_joint(cdps, scopes, card):
    """Łączy lokalne CPD w pełny rozkład łączny sieci."""
    n = len(card)
    J = np.ones([1]*n)
    for cdp, scope in zip(cdps, scopes):
        order = np.argsort(scope)
        arr = np.transpose(cdp, order)
        shape = [1] * n

        for ax, size in zip(np.asarray(scope)[order], arr.shape):
            shape[ax] = size

        J = J * arr.reshape(shape)

    return J



# KROK 6: Obliczanie zliczeń dla rodzin
def _family_expected_counts(Q, miss, code, scope, card):
    """Oblicza oczekiwane zliczenia dla jednej rodziny, uwzględniając braki."""
    scope_sorted = sorted(scope)
    drop = tuple(k for k, ax in enumerate(miss) if ax not in scope)
    M = Q.sum(axis=drop) if drop else Q      # osie = brakujące z rodziny, rosnąco
    E = np.zeros([card[ax] for ax in scope_sorted])
    idx = tuple(slice(None) if code[ax] < 0 else int(code[ax]) for ax in scope_sorted)
    E[idx] = M                               # indeksowanie int usuwa oś obserwowaną
    perm = [scope_sorted.index(ax) for ax in scope]
    return E.transpose(perm)                 # kolejność: rodzice..., X


# KROK 7: Krok E
def _e_step(cpds, scopes, card, patterns, counts):
    """Oblicza oczekiwane zliczenia CPD oraz log-wiarygodność danych."""
    n = len(card)
    J = _build_joint(cpds, scopes, card)
    N = [np.zeros(c.shape) for c in cpds]     # oczekiwane zliczenia
    L = 0.0
    for code, cnt in zip(patterns, counts):
        code = np.atleast_1d(code)
        idx = tuple(slice(None) if c < 0 else int(c) for c in code)
        Q = np.asarray(J[idx], dtype=float)   # P(obserwacje, braki)
        p_r = Q.sum()                         # P(obserwacje)
        if not np.isfinite(p_r) or p_r <= 0:
            raise ValueError(
                f"Observed pattern {code.tolist()} has zero or invalid probability "
                "under the current CPDs"
            )
        L += cnt * np.log(max(p_r, 1e-300))   # log-wiarygodność; ochrona przed log(0)
        Q = Q / p_r                           # posterior brakujących zmiennych
        miss = [i for i in range(n) if code[i] < 0]
        for i in range(n):
            N[i] += cnt * _family_expected_counts(Q, miss, code, scopes[i], card)
    return N, L


# KROK 8: Krok M
def _m_step(N):
    """Aktualizuje CPD przez normalizację oczekiwanych zliczeń."""
    new = []
    for Ni in N:
        S = Ni.sum(axis=-1, keepdims=True)
        uniform = np.full_like(Ni, 1.0 / Ni.shape[-1])
        new.append(np.where(S > 0, Ni / np.where(S > 0, S, 1.0), uniform))
    return new

# Pełna pętla EM
def _run_em(scopes, card, patterns, counts, n_rows, max_iter, tol, rng, cpds0=None):
    """Powtarza kroki E i M aż do zbieżności lub limitu iteracji."""
    cpds = cpds0 if cpds0 is not None else [_random_cdp(card[s], rng) for s in scopes]
    history, L_prev = [], None
    for it in range(max_iter):
        N, L = _e_step(cpds, scopes, card, patterns, counts)
        history.append(L)
        if L_prev is not None and L < L_prev - 1e-9 * (1 + abs(L_prev)):
            warnings.warn(f"L zmalała w iteracji {it}: {L_prev:.8f} -> {L:.8f}")
        cpds = _m_step(N)
        if L_prev is not None and abs(L - L_prev) < tol * n_rows:
            break
        L_prev = L
    # Oblicz wiarygodność końcowych CPD po ostatnim kroku M.
    _, final_L = _e_step(cpds, scopes, card, patterns, counts)
    history.append(final_L)
    return cpds, history


def learn_cpds_em(data: Data, parents: Dict[str, List[str]], max_iter: int=100, tol: float=1e-6,
                   n_restarts:int =5, init: str = "random", seed: int = 0,
                   state_names: Dict[str, List[str]] = None):
    """
    Uczy tablice CPD z danych z brakami za pomocą algorytmu EM.

    Parametry:
    - data: obiekt data z danymi do estymacji cdp
    - parents: słownik mapujący każdą zmienną na listę jej rodziców, np. {'A': [], 'B': ['A']}
    - max_iter: maksymalna liczba iteracji
    - tol: próg zbieżności
    - state_names: opcjonalne jawne stany dla zmiennych, gdy nie wynikają z dtype

    Zwraca listę TabularCPD kompatybilną z pgmpy oraz historię (tablicę z logami wiarygodności)
    """

    if data.data_purpose == DataPurpose.Test:
        raise ValueError("Training or estimation should not be performed on test data")

    if not isinstance(max_iter, (int, np.integer)) or max_iter < 1:
        raise ValueError("max_iter must be a positive integer")
    if not isinstance(n_restarts, (int, np.integer)) or n_restarts < 1:
        raise ValueError("n_restarts must be a positive integer")
    if not np.isfinite(tol) or tol < 0:
        raise ValueError("tol must be a finite non-negative number")
    if init not in ("random", "counts"):
        raise ValueError("init must be 'random' or 'counts'")

    # KROK 1: Przygotowanie danych i dziedzin zmiennych
    df = data.data_frame
    variables = list(parents.keys())
    if not variables:
        raise ValueError("parents must define at least one variable")
    if set(df.columns) != set(variables):
        raise ValueError(
            "Data columns must match the variables defined in parents"
        )
    if len(df) == 0:
        raise ValueError("Cannot estimate CPDs from an empty data frame")

    for variable, variable_parents in parents.items():
        if not isinstance(variable_parents, (list, tuple)):
            raise ValueError(f"Parents of {variable} must be a list or tuple")
        if len(variable_parents) != len(set(variable_parents)):
            raise ValueError(f"Variable {variable} has duplicate parents")
        if variable in variable_parents:
            raise ValueError(f"Variable {variable} cannot be its own parent")
        unknown = [parent for parent in variable_parents if parent not in parents]
        if unknown:
            raise ValueError(
                f"Variable {variable} has unknown parent(s): {', '.join(unknown)}"
            )

    # A product of local CPDs is a normalized joint distribution only for a DAG.
    state = {variable: 0 for variable in variables}

    def visit(variable):
        """Sprawdza cykle, przechodząc po rodzicach zmiennej."""
        if state[variable] == 1:
            raise ValueError("Parent graph must be directed acyclic")
        if state[variable] == 2:
            return
        state[variable] = 1
        for parent in parents[variable]:
            visit(parent)
        state[variable] = 2

    for variable in variables:
        visit(variable)

    var_idx = {v:i for i, v in enumerate(variables)} # kodowanie zmiennej liczbą całkowitą (indeksem)
    n_rows, n  = len(df), len(variables)

    if state_names is not None and set(state_names) != set(variables):
        raise ValueError("state_names must define exactly the variables in parents")

    domains = {}
    for variable in variables:
        if state_names is not None:
            domain = list(state_names[variable])
        elif isinstance(df[variable].dtype, pd.CategoricalDtype):
            domain = list(df[variable].cat.categories)
        else:
            domain = sorted(df[variable].dropna().unique().tolist())

        if not domain:
            raise ValueError(
                f"Variable {variable} is all-missing and has no declared states"
            )
        if len(domain) != len(set(domain)):
            raise ValueError(f"Variable {variable} has duplicate declared states")
        observed = df[variable].dropna().unique().tolist()
        if any(value not in domain for value in observed):
            raise ValueError(f"Data for {variable} contains a state not in its domain")
        domains[variable] = domain

    card = np.array([len(domains[v]) for v in variables]) # Cardinality-liczba stanów danej zmiennej


    # KROK 1 (ciąg dalszy): Kodowanie stanów jako indeksów liczbowych
    codes = np.full((n_rows, n), -1, dtype=np.int64)
    for v in variables:
        mapping = {val: k for k, val in enumerate(domains[v])}
        codes[:, var_idx[v]] = (
            df[v].astype(object).map(mapping).fillna(-1).astype(np.int64).values
        )


    # KROK 2: Grupowanie powtarzających się wierszy
    patterns, counts = np.unique(codes, axis=0, return_counts=True)

    # KROK 3: Przygotowanie układów tablic CPD
    scopes = [[var_idx[p] for p in parents[v]] + [var_idx[v]] for v in variables]

    rng = np.random.default_rng(seed)
    results = []
    history = []
    for r in range(n_restarts):
        cdps0 = _count_init(scopes, card, codes) if (init == "counts" and r == 0) else None
        cdps, hist = _run_em(scopes, card, patterns, counts, n_rows, max_iter, tol, rng, cdps0)
        history.append(hist)

        results.append((hist[-1], cdps))

    best_likelihood, best_cpds = results[0]
    for likelihood, candidate_cpds in results[1:]:
        tie_tolerance = 1e-10 * (1 + abs(best_likelihood))
        if likelihood > best_likelihood + tie_tolerance:
            best_likelihood, best_cpds = likelihood, candidate_cpds

    cpds = []
    for i, variable in enumerate(variables):
        variable_parents = parents[variable]
        family = best_cpds[i]
        values = family.reshape(-1, int(card[i])).T
        kwargs = {
            "variable": variable,
            "variable_card": int(card[i]),
            "values": values,
            "state_names": {
                name: domains[name] for name in [variable, *variable_parents]
            },
        }
        if variable_parents:
            kwargs["evidence"] = variable_parents
            kwargs["evidence_card"] = [len(domains[parent]) for parent in variable_parents]
        cpds.append(TabularCPD(**kwargs))

    return cpds, history
