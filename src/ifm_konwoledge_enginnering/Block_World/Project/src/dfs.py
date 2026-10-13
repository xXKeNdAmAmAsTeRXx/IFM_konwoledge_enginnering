import numpy as np

from .BlockState import BlockState


def dfs(state:BlockState, max_visited_notes = 1000):

    if np.array_equal(state.current, state.goal):
        return [state.current]

    pass
