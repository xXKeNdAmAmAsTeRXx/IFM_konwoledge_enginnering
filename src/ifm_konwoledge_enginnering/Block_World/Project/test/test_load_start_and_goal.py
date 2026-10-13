import pytest
import numpy as np

from ifm_konwoledge_enginnering.Block_World.Project.src import LoadStartAndGoal as loader_module
from ifm_konwoledge_enginnering.Block_World.Project.src.LoadStartAndGoal import (
    LoadStartAndGoal,
)


class CapturedWorld:
    """Lightweight World substitute so these tests isolate file parsing."""

    def __init__(self, placement):
        self.placement = np.asarray(placement)


def write_layouts(tmp_path, text):
    path = tmp_path / "layouts.txt"
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_start_and_goal_worlds(tmp_path, monkeypatch):
    monkeypatch.setattr(loader_module, "World", CapturedWorld)
    path = write_layouts(
        tmp_path,
        "# start layout\n0 1 0\n\n# goal layout\n0 0 0\n",
    )

    layouts = LoadStartAndGoal.load_from_txt(path)

    assert isinstance(layouts.start, CapturedWorld)
    assert isinstance(layouts.goal, CapturedWorld)
    assert layouts.start.placement.tolist() == [0, 1, 0]
    assert layouts.goal.placement.tolist() == [0, 0, 0]


def test_loads_layout_file_with_utf8_bom(tmp_path, monkeypatch):
    monkeypatch.setattr(loader_module, "World", CapturedWorld)
    path = tmp_path / "layouts.txt"
    path.write_bytes(b"\xef\xbb\xbf0 0\n0 1\n")

    layouts = LoadStartAndGoal.load_from_txt(path)

    assert layouts.start.placement.tolist() == [0, 0]
    assert layouts.goal.placement.tolist() == [0, 1]


@pytest.mark.parametrize(
    "content",
    [
        "",
        "# no layouts\n",
        "0 0\n",
        "0 0\n0 0\n0 0\n",
    ],
)
def test_rejects_files_without_exactly_two_layouts(tmp_path, content):
    path = write_layouts(tmp_path, content)

    with pytest.raises(ValueError, match="expected 2 layout lines"):
        LoadStartAndGoal.load_from_txt(path)


@pytest.mark.parametrize("content", ["0 x\n0 0\n", "0 0\n0 1.5\n"])
def test_rejects_non_integer_layout_values(tmp_path, content):
    path = write_layouts(tmp_path, content)

    with pytest.raises(ValueError, match="must contain only integers"):
        LoadStartAndGoal.load_from_txt(path)


def test_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        LoadStartAndGoal.load_from_txt(tmp_path / "missing.txt")
