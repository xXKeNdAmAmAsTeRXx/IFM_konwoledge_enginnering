import numpy as np

from .World import World


def dfs(start: World, goal: World, max_visited_notes = 1000):
    # TODO: Validate that start and goal contain the same number of blocks and
    #       compare their placements. If they already match, return an empty path.
    # TODO: Use tuple(world.placement) as the immutable key for each search state.
    # TODO: Implement depth-first search with an explicit stack (to avoid Python's
    #       recursion limit), a visited set, and a parent map storing each state's
    #       predecessor plus the Move used to reach it.
    # TODO: Ask World for legal moves instead of duplicating block-clearance and
    #       placement rules here. Build each successor without mutating start or
    #       another state that is already on the stack.
    # TODO: Mark states visited when adding them to the stack so duplicate paths
    #       cannot add the same placement repeatedly.
    # TODO: Order moves deterministically, trying moves that put a block onto its
    #       goal support first; document this ordering for the project report.
    # TODO: Count expanded states and stop when max_visited_notes is exceeded.
    #       Raise or return a distinct, clear search-limit result rather than
    #       reporting it as an ordinary no-solution result.
    # TODO: When the goal is found, reconstruct and return the Move sequence by
    #       following the parent map back to the start. Also expose the expanded
    #       count and elapsed time for the required experiment report.
    pass
