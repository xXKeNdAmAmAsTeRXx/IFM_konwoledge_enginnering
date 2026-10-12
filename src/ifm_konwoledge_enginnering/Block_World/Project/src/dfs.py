import numpy as np

from src.ifm_konwoledge_enginnering.Block_World.Project.src import BlockState


def dfs(state:BlockState, max_visited_notes = 1000):

    if np.array_equal(state.current, state.goal):
        return [state.current]

    pass