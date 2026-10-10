"""Tests for BlockState.load_from_txt (Projekt 1 - swiat klockow).

Scope: reading and parsing the input FILE only.
  * two meaningful lines: start layout, then goal layout
  * blank lines and lines starting with '#' are skipped
  * each layout is N integers separated by whitespace
Validation of the layouts themselves (self-loops, cycles, two blocks on one
block, ...) is covered by other tests.

load_from_txt returns ONE BlockState object built as BlockState(start, goal).

ASSUMPTIONS - adjust the things marked "ADJUST" to match your code:
  1. module / class name           -> import below
  2. how to read start and goal    -> `start_layout()` / `goal_layout()` below
  3. file-format errors are raised as ValueError
"""
import pytest

from src.ifm_konwoledge_enginnering.Block_World.Project.src.BlockState import BlockState  # ADJUST: module name


def start_layout(state):
    """Return the start layout as the list from the file format:
    item i-1 = block that block i lies on (0 = table).

    ADJUST: change `state.start` to whatever your class exposes.
    """
    return list(state.start)


def goal_layout(state):
    """Same as start_layout, but for the goal layout.

    ADJUST: change `state.goal` to whatever your class exposes.
    """
    return list(state.goal)


def write_input(tmp_path, text, name="input.txt"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return str(path)


# --------------------------------------------------------------------------
# Happy path
# --------------------------------------------------------------------------

def test_loads_example_from_assignment(tmp_path):
    path = write_input(
        tmp_path,
        "# start: [1 2 4] [3 5]\n"
        "0 1 0 2 3\n"
        "# cel: wieza [5 4 3 2 1] (5 na dole)\n"
        "2 3 4 5 0\n",
    )

    state = BlockState.load_from_txt(path)

    assert isinstance(state, BlockState)
    assert start_layout(state) == [0, 1, 0, 2, 3]
    assert goal_layout(state) == [2, 3, 4, 5, 0]


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("0 1 0\n0 0 0\n", id="plain"),
        pytest.param("0 1 0\n0 0 0", id="no-trailing-newline"),
        pytest.param("# c1\n0 1 0\n# c2\n0 0 0\n", id="comments"),
        pytest.param("#no-space-comment\n0 1 0\n#\n0 0 0\n", id="comment-variants"),
        pytest.param("\n\n0 1 0\n\n\n0 0 0\n\n", id="blank-lines"),
        pytest.param("   \n0 1 0\n\t\n0 0 0\n", id="whitespace-only-lines"),
        pytest.param("0   1   0  \n\t0 0 0\t\n", id="extra-whitespace"),
        pytest.param("0 1 0\r\n0 0 0\r\n", id="crlf"),
    ],
)
def test_skips_comments_blanks_and_tolerates_whitespace(tmp_path, text):
    path = write_input(tmp_path, text)

    state = BlockState.load_from_txt(path)

    assert start_layout(state) == [0, 1, 0]
    assert goal_layout(state) == [0, 0, 0]


def test_file_with_bom_is_read(tmp_path):
    path = tmp_path / "bom.txt"
    path.write_bytes(b"\xef\xbb\xbf0 1 0\n0 0 0\n")

    state = BlockState.load_from_txt(str(path))

    assert start_layout(state) == [0, 1, 0]
    assert goal_layout(state) == [0, 0, 0]


def test_first_line_is_start_and_second_is_goal(tmp_path):
    path = write_input(tmp_path, "0 0 0\n0 1 2\n")

    state = BlockState.load_from_txt(path)

    assert start_layout(state) == [0, 0, 0]
    assert goal_layout(state) == [0, 1, 2]


def test_single_block(tmp_path):
    path = write_input(tmp_path, "0\n0\n")

    state = BlockState.load_from_txt(path)

    assert start_layout(state) == [0]
    assert goal_layout(state) == [0]


def test_accepts_path_with_directories_and_unicode_comments(tmp_path):
    sub = tmp_path / "przyklady"
    sub.mkdir()
    path = write_input(sub, "# układ początkowy: wieża\n0 1 2\n# cel: wszystko na stole\n0 0 0\n")

    state = BlockState.load_from_txt(path)

    assert start_layout(state) == [0, 1, 2]
    assert goal_layout(state) == [0, 0, 0]


# --------------------------------------------------------------------------
# Malformed files
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        pytest.param("0 a 0\n0 0 0\n", id="letter-token"),
        pytest.param("0 1.5 0\n0 0 0\n", id="float-token"),
        pytest.param("0 0 0\n0 x 0\n", id="non-integer-in-goal"),
        pytest.param("[0 1 0]\n0 0 0\n", id="brackets"),
    ],
)
def test_non_integer_tokens_are_rejected(tmp_path, text):
    path = write_input(tmp_path, text)

    with pytest.raises(ValueError) as exc_info:
        BlockState.load_from_txt(path)

    assert str(exc_info.value).strip(), "error message must not be empty"


@pytest.mark.parametrize(
    "text",
    [
        pytest.param("", id="empty-file"),
        pytest.param("# only a comment\n\n", id="only-comments-and-blanks"),
        pytest.param("0 1 0\n", id="only-start"),
        pytest.param("0 1 0\n0 0 0\n0 0 0\n", id="three-layouts"),
    ],
)
def test_wrong_number_of_layout_lines_is_rejected(tmp_path, text):
    path = write_input(tmp_path, text)

    with pytest.raises(ValueError) as exc_info:
        BlockState.load_from_txt(path)

    assert str(exc_info.value).strip()


def test_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        BlockState.load_from_txt(str(tmp_path / "does_not_exist.txt"))