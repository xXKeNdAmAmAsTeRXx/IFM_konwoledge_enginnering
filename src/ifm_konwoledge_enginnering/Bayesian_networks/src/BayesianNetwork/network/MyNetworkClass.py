from typing import List, Tuple, Dict

import numpy as np
import pandas as pd
from pgmpy.estimators import BIC
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.parameter_estimator import DiscreteMLE
from pgmpy.inference import VariableElimination
from pgmpy.causal_discovery import ExpertKnowledge, HillClimbSearch


from BayesianNetwork.models.data import Data, DataPurpose
from BayesianNetwork.models.graph import GraphData
from BayesianNetwork.models.queries import Query, QueryType
from BayesianNetwork.models.variable import Variable


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

    @staticmethod
    def learn_structure_HC(training_data: Data, expert: ExpertKnowledge | None = None):
        """
        If drop na is false data is estimated by EM algorithm
        """

        assert training_data.data_purpose == DataPurpose.Train, "Do not train model on test data"

        hc = HillClimbSearch(
            scoring_method="bic-d",
            expert_knowledge=expert,
            return_type="dag",
            max_indegree=4,
            show_progress=False,
        )

        df = training_data.data_frame
        train_df = df.dropna()

        hc.fit(train_df)
        g = hc.causal_graph_

        return hc.causal_graph_, BIC(train_df).score(g)

    @classmethod
    def build_network(cls, training_data: Data, variables_dict: Dict[str, Variable], expert: ExpertKnowledge | None = None):
        dag, _ = cls.learn_structure_HC(training_data, expert)
        model = DiscreteBayesianNetwork(list(dag.edges))
        mle = DiscreteMLE(state_names = {n: v.states for n, v in variables_dict.items()}).fit(model, training_data.data_frame)

        return cls(model, mle.parameters_)


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

    def score_on_variable(self, test_data: Data, variable_name:str) -> float:
        """
        Network Predicts (via MAP) the given variable name for each row and return accuracy
        """

        assert test_data.data_purpose is DataPurpose.Test, "Do not test model on train data"
        df = test_data.data_frame

        model = self.network
        infer = VariableElimination(model)

        correct_quesses = 0
        for _, row in df.iterrows():
            obs = {v: row[v] for v in model.nodes() if pd.notna(row[v])}
            del obs[variable_name]

            map = infer.map_query([variable_name],evidence = obs, show_progress=False)
            value = map[variable_name]

            if value == row[variable_name]:
                correct_quesses += 1

        return correct_quesses/len(df)