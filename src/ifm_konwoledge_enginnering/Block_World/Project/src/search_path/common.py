"""Shared state handling and graph-search logic for Block World."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Literal

from ..Move import Move
from ..World import World

StateKey = tuple[int, ...]
SearchStrategy = Literal["bfs", "dfs"]


@dataclass
class SearchResult:
    """Path and basic statistics returned by a search.

    ``peak_stored_states`` is the maximum number of unique states retained in
    the visited set during the run.
    """

    path: list[Move]
    expanded: int
    elapsed: float
    peak_stored_states: int


class SearchLimitExceeded(RuntimeError):
    """Search limit error carrying the statistics collected before stopping."""

    def __init__(
        self,
        limit: int,
        expanded: int,
        peak_stored_states: int,
        elapsed: float,
    ):
        super().__init__(f"Search limit exceeded: {limit} nodes expanded")
        self.expanded = expanded
        self.peak_stored_states = peak_stored_states
        self.elapsed = elapsed


def state_key(world: World) -> StateKey:
    """Return a hashable key for a world placement."""
    return tuple(int(block) for block in world.placement)


def order_moves(moves: list[Move], goal: World) -> list[Move]:
    """Order moves deterministically, trying goal-consistent moves first."""

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


def search_with_stats(
    start: World,
    goal: World,
    max_visited_notes: int = 1000,
    extended: bool = False,
    strategy: SearchStrategy = "bfs",
) -> SearchResult:
    """Search the state graph using BFS or DFS and return path statistics."""
    if len(start) != len(goal):
        raise ValueError("start and goal must have the same number of blocks")
    if strategy not in ("bfs", "dfs"):
        raise ValueError(f"Unknown search strategy: {strategy}")

    started_at = time.perf_counter()
    start_key = state_key(start)
    goal_key = state_key(goal)

    if start_key == goal_key:
        return SearchResult([], 0, time.perf_counter() - started_at, 1)

    if strategy == "bfs":
        frontier: deque[World] | list[World] = deque([World(start.placement.copy())])
    else:
        frontier = [World(start.placement.copy())]

    visited: set[StateKey] = {start_key}
    parent: dict[StateKey, tuple[StateKey, Move]] = {}
    expanded = 0
    peak_stored_states = len(visited)

    while frontier:
        if expanded >= max_visited_notes:
            raise SearchLimitExceeded(
                max_visited_notes,
                expanded,
                peak_stored_states,
                time.perf_counter() - started_at,
            )

        world = frontier.popleft() if strategy == "bfs" else frontier.pop()
        world_key = state_key(world)
        expanded += 1

        moves = order_moves(world.legal_moves(extended), goal)
        # DFS uses a LIFO frontier, so reverse the order to try the best move first.
        if strategy == "dfs":
            moves.reverse()

        for move in moves:
            child = World(world.placement.copy())
            child.update(move)
            child_key = state_key(child)

            if child_key in visited:
                continue

            visited.add(child_key)
            peak_stored_states = max(peak_stored_states, len(visited))
            parent[child_key] = (world_key, move)

            if child_key == goal_key:
                path = reconstruct_path(parent, start_key, goal_key)
                return SearchResult(
                    path,
                    expanded,
                    time.perf_counter() - started_at,
                    peak_stored_states,
                )

            frontier.append(child)

    raise RuntimeError("No solution exists for this start and goal")
