"""Breadth-first search for shortest Block World move sequences."""

from ..Move import Move
from ..World import World
from .common import SearchResult, search_with_stats


def bfs_with_stats(
    start: World,
    goal: World,
    max_visited_notes: int = 1000,
    extended: bool = False,
) -> SearchResult:
    """Run breadth-first search and return the path with search statistics."""
    return search_with_stats(
        start,
        goal,
        max_visited_notes=max_visited_notes,
        extended=extended,
        strategy="bfs",
    )


def bfs(
    start: World,
    goal: World,
    max_visited_notes: int = 1000,
    extended: bool = False,
) -> list[Move]:
    """Return a shortest move sequence from start to goal using BFS."""
    return bfs_with_stats(start, goal, max_visited_notes, extended).path
