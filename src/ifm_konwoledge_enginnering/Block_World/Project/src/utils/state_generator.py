import numpy as np

from ..World import World
from .LoadStartAndGoal import LoadStartAndGoal

def world_generator(n_blocks: int, rng: np.random.Generator) -> World:
    if n_blocks < 1:
        raise ValueError("n_blocks must be positive")

    order = rng.permutation(np.arange(1, n_blocks + 1))
    placement = np.zeros(n_blocks, dtype=np.int32)

    # The first block starts on the table.
    # Later blocks either start on another stack or go on the preceding block.
    for i in range(1, n_blocks):
        if rng.random() >= 0.35:
            block = int(order[i])
            support = int(order[i - 1])
            placement[block - 1] = support

    return World(placement)
def start_goal_generator(n_blocks:int, seed:int = 42) -> LoadStartAndGoal:
    rng = np.random.default_rng(seed)

    start = world_generator(n_blocks, rng)
    goal = world_generator(n_blocks, rng)

    return LoadStartAndGoal(start, goal)
