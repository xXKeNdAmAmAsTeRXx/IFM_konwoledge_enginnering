import json

import pytest


@pytest.fixture
def integration_dataset(tmp_path):
    """Create a small, self-contained dataset for end-to-end parser tests."""
    description = {
        "variables": {
            "D": {"description": "course difficulty", "states": ["Easy", "Hard"]},
            "I": {"description": "student intelligence", "states": ["Dumb", "Intelligent"]},
            "G": {"description": "course grade", "states": ["A", "B", "C"]},
            "S": {"description": "SAT score", "states": ["Bad", "Good"]},
            "L": {"description": "recommendation letter", "states": ["Bad", "Good"]},
        },
        "expert_edges": [["D", "G"], ["I", "G"], ["G", "L"], ["I", "S"]],
        "required_edges": [["D", "G"], ["G", "L"]],
        "forbidden_edges": [["D", "I"], ["S", "L"]],
        "tiers": [["D", "I"], ["G", "S"], ["L"]],
    }
    (tmp_path / "opis.json").write_text(
        json.dumps(description, ensure_ascii=False), encoding="utf-8"
    )
    (tmp_path / "dane.csv").write_text(
        "D,I,G,S,L\n"
        "Easy,Dumb,A,Bad,Good\n"
        "Hard,Intelligent,C,Good,Bad\n"
        "Easy,Intelligent,B,Good,Good\n"
        "Hard,,C,Bad,Bad\n"
        ",Dumb,A,,Good\n",
        encoding="utf-8",
    )
    (tmp_path / "test.csv").write_text(
        "D,I,G,S,L\n"
        "Easy,Dumb,A,Bad,Good\n"
        "Hard,Intelligent,C,Good,Bad\n"
        "Easy,Intelligent,B,Good,Good\n",
        encoding="utf-8",
    )
    (tmp_path / "zapytania.txt").write_text(
        "# Integration test queries\n"
        "P(G)\n"
        "P(G | D == Easy)\n"
        "MAP(I | G == A)\n"
        "P(D, I | G == B)\n",
        encoding="utf-8",
    )

    return tmp_path
