from typing import List

import numpy as np
import pandas as pd
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.parameter_estimator import DiscreteMLE
from pgmpy.inference import VariableElimination

from BayesianNetwork.models.data import Data, DataPurpose
from BayesianNetwork.models.graph import GraphData
from BayesianNetwork.models.queries import Query, QueryType


class MyNetworkClass:

    def __init__(self, network: DiscreteBayesianNetwork, cdps: List[TabularCPD]):
        self.network = network
        self.network.add_cpds(*cdps)
        self.cdps = cdps

        if not network.check_model():
            raise Exception("Model Definition is not correct")

    def get_model(self):
        return self.network

    @classmethod
    def build_from_expert_graph(cls, graph: GraphData, training_data: Data):

        assert training_data.data_purpose == DataPurpose.Train, "Do not train model on test data"

        network = DiscreteBayesianNetwork(graph.exper_edges)
        mle = DiscreteMLE(state_names = {n : v.states for n, v in graph.variables_dict.items()}).fit(network, training_data.data_frame)

        return cls(network, mle.parameters_)

    def get_biggest_cdp(self):
        # Assume that biggest table is the one with the most values
        biggest_cdp = max(self.cdps, key=lambda x: x.get_values().size)

        return biggest_cdp

    def answer_question(self, query: Query):
        network_infer = VariableElimination(self.network)

        variable = query.variables
        evidence = query.evidence

        if query.query_type == QueryType.P:
            answers = network_infer.query(variable, evidence, show_progress=False)
        else:
            answers = network_infer.map_query(variable, evidence, show_progress=False)

        return answers

    def score(self, test_data: Data) -> tuple[float, List[float], int]:
        """
        This function makes a prediction for each row in given test data.
        Return: mean log of probability that row exist and count of rows that are impossible (zero)
        """
        assert test_data.data_purpose is DataPurpose.Test, "Do not test model on train data"
        df = test_data.data_frame

        model = self.network
        infer = VariableElimination(model)

        log = []
        P_sum = 0
        zeros_count = 0
        for _, row in df.iterrows():
            obs = {v: row[v] for v  in model.nodes() if pd.notna(row[v])}
            phi = infer.query(obs, joint=True, show_progress=False)
            p = phi.get_value(**obs)

            if p == 0:
                zeros_count += 1
            else:
                log.append(np.log(max(p, 10e-10)))
                P_sum += p

        return P_sum/len(log), sum(log) / len(log), zeros_count