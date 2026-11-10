from typing import Dict, List
from pgmpy.models import DiscreteBayesianNetwork
from pgmpy.factors.discrete import TabularCPD

from models.data import Data
from models.graph import GraphData
from models.variable import Variable


class BayesianNetwork:

    def __init__(self, network: DiscreteBayesianNetwork, cdps: List[TabularCPD]):
        self.network = network.add_cpds(*cdps)

    @classmethod
    def build_from_expert_graph(self, graph: GraphData):
        #TODO: Build a network from expert graph with uniform distribution

        network = DiscreteBayesianNetwork(graph.exper_edges)

        cdp_list = []
        #TODO: CPD list with uniform distribution (needs to be based on expert graph)
        #Idea 1: Go trough expert graph edges and map parents-children
        #Idea 2: Use Tiers and search parents with assumptions

        raise NotImplementedError

        self.__init__(network, cdp_list)

    def estimate_cdps(self, data: Data) -> None:
        #TODO: estimate and update cdps
        pass
