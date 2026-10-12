import numpy as np

from src.ifm_konwoledge_enginnering.Block_World.Project.src import BlockState


def dfs(state:BlockState):

    if np.array_equal(state.current, state.goal):
        return [state.current]


    # dziecko : rodzic
    parent = {
        state.current: None,

    }

    stack = [state]
    visited = set()

    while stack:
        current = state
      state.update_move()