from typing import List

def check_for_cycles(edges: List[tuple[str, str]]) -> bool:
    """Detects cycles in a directed graph using DFS recursion stack."""
    graph = {}
    for u, v in edges:
        graph.setdefault(u, []).append(v)

    visited = set()
    rec_stack = set()

    def dfs(node):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        rec_stack.remove(node)
        return False

    for node in graph:
        if node not in visited:
            if dfs(node):
                return True
    return False