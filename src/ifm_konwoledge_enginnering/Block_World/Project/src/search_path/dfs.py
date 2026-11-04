from __future__ import annotations

from .common import (
    SearchResult,
    StateKey,
    order_moves,
    reconstruct_path,
    search_with_stats,
    state_key,
)
from ..Move import Move
from ..World import World


def dfs_with_stats(
    start: World,
    goal: World,
    max_visited_notes: int = 1000,
    extended: bool = False,
) -> SearchResult:
    """Run depth-first search and return the path with search statistics."""
    return search_with_stats(
        start,
        goal,
        max_visited_notes=max_visited_notes,
        extended=extended,
        strategy="dfs",
    )


def dfs(
    start: World,
    goal: World,
    max_visited_notes: int = 1000,
    extended: bool = False,
) -> list[Move]:
    """Return only the move sequence found by depth-first search."""
    return dfs_with_stats(start, goal, max_visited_notes, extended).path
