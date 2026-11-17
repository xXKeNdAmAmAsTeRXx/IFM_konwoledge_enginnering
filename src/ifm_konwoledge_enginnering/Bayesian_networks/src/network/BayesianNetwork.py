from typing import List
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD
from pgmpy.parameter_estimator import DiscreteMLE

from models.data import Data
from models.graph import GraphData
from models.queries import Query


class BayesianNetwork:

    def __init__(self, network: DiscreteBayesianNetwork, cdps: List[TabularCPD]):
        self.network = network.add_cpds(*cdps)
        self.cdps = cdps

    @classmethod
    def build_from_expert_graph(self, graph: GraphData, training_data: List[Data]):
        network = DiscreteBayesianNetwork(graph.exper_edges)

        mle = DiscreteMLE().fit(network, training_data)
        cpds = mle.parameters_

        self.__init__(network, cpds)

    def get_biggest_cdp(self):
        # TODO: Get biggest cdp and count paranets/rows
        pass

    def answer_question(self, query: Query):
        #TODO: implement query answear
        pass