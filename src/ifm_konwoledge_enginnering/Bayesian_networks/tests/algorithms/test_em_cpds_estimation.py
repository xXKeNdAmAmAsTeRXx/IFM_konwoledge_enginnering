import numpy as np
import pandas as pd
import pytest

from BayesianNetwork.algorithms.em_cdps_estimation import learn_cpds_em
from BayesianNetwork.models.data import Data, DataPurpose


def _cpds_by_variable(cpds):
    return {cpd.variable: cpd for cpd in cpds}


def test_complete_data_recovers_empirical_cpds_and_state_names():
    data = Data(
        DataPurpose.Train,
        pd.DataFrame(
            {
                "A": ["a0", "a0", "a1", "a1"],
                "B": ["b0", "b1", "b1", "b1"],
            }
        ),
    )

    cpds = _cpds_by_variable(
        learn_cpds_em(data, {"A": [], "B": ["A"]}, max_iter=20)
    )

    np.testing.assert_allclose(cpds["A"].get_values()[:, 0], [0.5, 0.5])
    np.testing.assert_allclose(
        cpds["B"].get_values(),
        [[0.5, 0.0], [0.5, 1.0]],
    )
    assert cpds["A"].state_names["A"] == ["a0", "a1"]
    assert cpds["B"].state_names["B"] == ["b0", "b1"]
    assert cpds["B"].state_names["A"] == ["a0", "a1"]


def test_missing_values_contribute_expected_counts_and_cpds_are_normalized():
    data = Data(
        DataPurpose.Train,
        pd.DataFrame(
            {
                "A": ["a", "a", "b", "b"],
                "B": ["x", None, "y", None],
            }
        ),
    )

    cpds = _cpds_by_variable(
        learn_cpds_em(data, {"A": [], "B": ["A"]}, max_iter=200, tol=1e-10)
    )

    b_values = cpds["B"].get_values()
    # pgmpy orders parent configurations according to A's state_names.
    a_states = cpds["B"].state_names["A"]
    a_column = a_states.index("a")
    b_column = a_states.index("b")
    x_row = cpds["B"].state_names["B"].index("x")
    y_row = cpds["B"].state_names["B"].index("y")

    assert b_values[x_row, a_column] > 0.99
    assert b_values[y_row, b_column] > 0.99
    for cpd in cpds.values():
        np.testing.assert_allclose(cpd.get_values().sum(axis=0), 1.0)


def test_declared_categorical_states_are_preserved():
    data = Data(
        DataPurpose.Train,
        pd.DataFrame(
            {
                "A": pd.Categorical(
                    ["low", "high", "low"],
                    categories=["low", "middle", "high"],
                )
            }
        ),
    )

    cpd = learn_cpds_em(data, {"A": []})[0]

    assert cpd.state_names["A"] == ["low", "middle", "high"]
    np.testing.assert_allclose(cpd.get_values().sum(axis=0), [1.0])


def test_fully_missing_row_preserves_cpds_with_reordered_family_axes():
    data = Data(
        DataPurpose.Train,
        pd.DataFrame(
            {
                "A": pd.Categorical([None], categories=["a0", "a1", "a2"]),
                "B": pd.Categorical([None], categories=["b0", "b1"]),
                "C": pd.Categorical([None], categories=["c0", "c1", "c2"]),
            }
        ),
    )
    parents = {"A": ["C", "B"], "B": [], "C": []}

    one_iteration = learn_cpds_em(data, parents, max_iter=1, seed=7)
    two_iterations = learn_cpds_em(data, parents, max_iter=2, seed=7)

    for first, second in zip(one_iteration, two_iterations):
        np.testing.assert_allclose(first.get_values(), second.get_values())


def test_rejects_test_data_and_invalid_parent_graph():
    test_data = Data(DataPurpose.Test, pd.DataFrame({"A": ["a"]}))
    with pytest.raises(ValueError, match="test data"):
        learn_cpds_em(test_data, {"A": []})

    train_data = Data(
        DataPurpose.Train,
        pd.DataFrame({"A": ["a", "b"], "B": ["x", "y"]}),
    )
    with pytest.raises(ValueError, match="directed acyclic"):
        learn_cpds_em(train_data, {"A": ["B"], "B": ["A"]})


def test_rejects_variable_with_no_observed_or_declared_states():
    data = Data(
        DataPurpose.Train,
        pd.DataFrame({"A": [None, np.nan]}),
    )

    with pytest.raises(ValueError, match="all-missing"):
        learn_cpds_em(data, {"A": []})
