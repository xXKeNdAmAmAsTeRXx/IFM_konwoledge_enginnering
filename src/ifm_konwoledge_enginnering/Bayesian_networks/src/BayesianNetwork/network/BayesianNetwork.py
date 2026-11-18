from typing import List
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.parameter_estimator import DiscreteMLE
from pgmpy.inference import VariableElimination

from BayesianNetwork.models.data import Data
from BayesianNetwork.models.graph import GraphData
from BayesianNetwork.models.queries import Query, QueryType


class BayesianNetwork:

    def __init__(self, network: DiscreteBayesianNetwork, cdps: List[TabularCPD]):
        self.network = network.add_cpds(*cdps)
        self.cdps = cdps

    def get_model(self):
        return self.network

    @classmethod
    def build_from_expert_graph(self, graph: GraphData, training_data: List[Data]):
        network = DiscreteBayesianNetwork(graph.exper_edges)

        mle = DiscreteMLE().fit(network, training_data)
        cpds = mle.parameters_

        self.__init__(network, cpds)

    def get_biggest_cdp(self):
        # Assume that biggest table is the one with the most values
        biggest_cdp = max(self.cdps, key=lambda x: x.value.shape[0] * x.value.shape[1])

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

