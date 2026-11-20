from typing import Dict

from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.parameter_estimator import DiscreteMLE

from BayesianNetwork.models.data import Data, DataPurpose
from BayesianNetwork.models.graph import GraphData
from .MyNetworkClass import MyNetworkClass


class IndependentNetworkModel(MyNetworkClass):
    """Bayesian network with all variables and no edges."""

    @classmethod
    def build_from_graph(cls, graph: GraphData, training_data: Data):
        if training_data.data_purpose is not DataPurpose.Train:
            raise ValueError("Do not train model on test data")

        network = DiscreteBayesianNetwork()
        network.add_nodes_from(graph.variables_dict)

        state_names = {
            name: variable.states
            for name, variable in graph.variables_dict.items()
        }
        mle = DiscreteMLE(state_names=state_names).fit(
            network,
            training_data.data_frame,
        )

        return cls(network, mle.parameters_)


class MostFrequentClassifier:
    """Constant classifier predicting each variable's most frequent train state."""

    def __init__(self, most_frequent_states: Dict[str, str]):
        self.most_frequent_states = dict(most_frequent_states)

    @classmethod
    def fit(cls, graph: GraphData, training_data: Data):
        if training_data.data_purpose is not DataPurpose.Train:
            raise ValueError("Do not train classifier on test data")

        data_frame = training_data.data_frame
        most_frequent_states = {}

        for name, variable in graph.variables_dict.items():
            if name not in data_frame.columns:
                raise ValueError(f"Training data is missing variable: {name}")

            counts = data_frame[name].value_counts(dropna=True)
            if counts.empty:
                raise ValueError(f"No observed training values for variable: {name}")

            # Respect the declared state order to break ties deterministically.
            most_frequent_states[name] = max(
                variable.states,
                key=lambda state: counts.get(state, 0),
            )

        return cls(most_frequent_states)

    def predict(self, variable_name: str) -> str:
        if variable_name not in self.most_frequent_states:
            raise ValueError(f"Unknown variable: {variable_name}")
        return self.most_frequent_states[variable_name]

    def score_on_variable(self, test_data: Data, variable_name: str) -> float:
        if test_data.data_purpose is not DataPurpose.Test:
            raise ValueError("Do not evaluate classifier on training data")
        if variable_name not in test_data.data_frame.columns:
            raise ValueError(f"Test data is missing variable: {variable_name}")

        actual_values = test_data.data_frame[variable_name].dropna()
        if actual_values.empty:
            raise ValueError(f"No observed test values for variable: {variable_name}")

        prediction = self.predict(variable_name)
        return float(actual_values.eq(prediction).mean())
