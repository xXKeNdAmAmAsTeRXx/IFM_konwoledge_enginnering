import pandas as pd
import pytest

from BayesianNetwork.models.data import Data, DataPurpose
from BayesianNetwork.models.graph import GraphData
from BayesianNetwork.models.variable import Variable
from BayesianNetwork.network.other_models import (
    IndependentNetworkModel,
    MostFrequentClassifier,
)


@pytest.fixture
def graph():
    variables = {
        "G": Variable("G", "grade", ["A", "B"]),
        "E": Variable("E", "evidence", ["x", "y"]),
    }
    return GraphData(
        variables_dict=variables,
        exper_edges=[("E", "G")],
        required_edges=[],
        forbidden_edges=[],
        tiers=[],
    )


@pytest.fixture
def train_data():
    return Data(
        DataPurpose.Train,
        pd.DataFrame(
            {
                "G": ["A", "A", "B", "A"],
                "E": ["x", "y", "x", "x"],
            }
        ),
    )


@pytest.fixture
def test_data():
    return Data(
        DataPurpose.Test,
        pd.DataFrame(
            {
                "G": ["A", "B", "A"],
                "E": ["y", "x", "x"],
            }
        ),
    )


def test_independent_model_keeps_nodes_but_removes_edges(graph, train_data):
    model = IndependentNetworkModel.build_from_graph(graph, train_data)

    assert set(model.network.nodes()) == set(graph.variables_dict)
    assert list(model.network.edges()) == []
    assert model.network.check_model()
    assert all(len(cpd.variables) == 1 for cpd in model.cdps)


def test_independent_model_scores_g_using_test_data(graph, train_data, test_data):
    model = IndependentNetworkModel.build_from_graph(graph, train_data)

    assert model.score_on_variable(test_data, "G") == pytest.approx(2 / 3)


def test_independent_model_rejects_test_data_for_training(graph, test_data):
    with pytest.raises(ValueError, match="test data"):
        IndependentNetworkModel.build_from_graph(graph, test_data)


def test_most_frequent_classifier_predicts_train_mode(graph, train_data):
    classifier = MostFrequentClassifier.fit(graph, train_data)

    assert classifier.predict("G") == "A"
    assert classifier.predict("E") == "x"


def test_most_frequent_classifier_accuracy_matches_independent_model(
    graph, train_data, test_data
):
    classifier = MostFrequentClassifier.fit(graph, train_data)
    independent_model = IndependentNetworkModel.build_from_graph(graph, train_data)

    assert classifier.score_on_variable(test_data, "G") == pytest.approx(2 / 3)
    assert classifier.score_on_variable(test_data, "G") == pytest.approx(
        independent_model.score_on_variable(test_data, "G")
    )


def test_most_frequent_classifier_rejects_test_data_for_fit(graph, test_data):
    with pytest.raises(ValueError, match="test data"):
        MostFrequentClassifier.fit(graph, test_data)
