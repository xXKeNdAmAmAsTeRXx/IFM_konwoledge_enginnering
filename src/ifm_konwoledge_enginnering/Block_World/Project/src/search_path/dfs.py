from __future__ import annotations

import time
import numpy as  np
from dataclasses import dataclass

from ..Move import Move
from ..World import World

StateKey = tuple[int, ...] # tablice Numpy są niehashowalne, więc nie da rady ich dać do set i dict

@dataclass
class SearchResult:
    """Store the outcome of a single search."""

    path: list[Move]
    expanded: int
    elapsed: float


def state_key(world: World) -> StateKey:
    return tuple(world.placement.tolist())


def order_moves(moves: list[Move], goal: World) -> list[Move]:
    """Order moves deterministically, goal-consistent moves first."""

    def is_not_goal_move(move: Move) -> bool:
        return goal.placement[move.moving - 1] != move.destination

    return sorted(moves, key=is_not_goal_move)


def reconstruct_path(
    parent: dict[StateKey, tuple[StateKey, Move]],
    start_key: StateKey,
    goal_key: StateKey,
) -> list[Move]:
    """Follow the parent map from the goal back to the start."""
    path: list[Move] = []
    key = goal_key
    while key != start_key:
        key, move = parent[key]
        path.append(move)
    path.reverse()
    return path


def dfs_with_stats(
    start: World,
    goal: World,
    max_visited_notes: int = 1000,
    extended: bool = False,
) -> SearchResult:
    """Run depth-first search and return the path with search statistics."""
    if len(start) != len(goal):
        raise ValueError("start and goal must have the same number of blocks")

    started_at = time.perf_counter()
    start_key = state_key(start)
    goal_key = state_key(goal)

    if start_key == goal_key:
        return SearchResult([], 0, time.perf_counter() - started_at)

    stack: list[World] = [start]
    visited: set[StateKey] = {start_key}
    parent: dict[StateKey, tuple[StateKey, Move]] = {}
    expanded = 0

    while stack:
        if expanded >= max_visited_notes:
            raise RuntimeError(
                f"Search limit exceeded: {max_visited_notes} nodes expanded"
            )

        world = stack.pop()
        expanded += 1
        world_key = state_key(world)

        moves = order_moves(world.legal_moves(extended), goal)
        # The stack is LIFO, so push the best move last to try it first.
        for move in reversed(moves):
            child = World(world.placement)
            child.update(move)
            child_key = state_key(child)

            if child_key in visited:
                continue

            visited.add(child_key)
            parent[child_key] = (world_key, move)

            if child_key == goal_key:
                path = reconstruct_path(parent, start_key, goal_key)
                return SearchResult(path, expanded, time.perf_counter() - started_at)

            stack.append(child)

    raise RuntimeError("No solution exists for this start and goal")


def dfs(
    start: World,
    goal: World,
    max_visited_notes: int = 1000,
    extended: bool = False,
) -> list[Move]:
    """Return only the move sequence found by depth-first search."""
    return dfs_with_stats(start, goal, max_visited_notes, extended).path