"""Console tool for manually exploring the sample Block World problem.

Run from the repository root with:
    uv run python -m ifm_konwoledge_enginnering.Block_World.Project.main
"""

from pathlib import Path

import numpy as np

from .src.BlockState import BlockState
from .src.LoadStartAndGoal import LoadStartAndGoal
from .src.Move import Move
from .src.World import World


SAMPLE_FILE = Path(__file__).parent / "src" / "data" / "correct_1.txt"


def show_world(label: str, world: World) -> None:
    """Print a placement and the status of each block."""
    print(f"\n{label} placement: {world.placement.tolist()}")
    for state in world.states:
        block: BlockState = state
        support = "table" if block.on_table else f"block {block.on}"
        print(
            f"  Block {block.id}: on {support}; "
            f"clear={block.clear}"
        )


def main() -> None:
    """Load the sample problem and accept manual block moves."""
    try:
        problem = LoadStartAndGoal.load_from_txt(SAMPLE_FILE)
    except (OSError, ValueError, AssertionError) as error:
        print(f"Could not load sample problem: {error}")
        return

    current = World(problem.start.placement.copy())
    goal = problem.goal

    print("Block World manual console")
    show_world("Start", current)
    show_world("Goal", goal)
    print(
        "\nCommands: show, move <block_id> <destination_id>, reset, quit. "
        "Use destination 0 for the table."
    )

    while True:
        try:
            command = input("\nblock-world> ").strip().split()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not command:
            continue

        action = command[0].lower()
        if action in {"quit", "q", "exit"}:
            break
        if action == "show":
            show_world("Current", current)
            print(f"Goal reached: {np.array_equal(current.placement, goal.placement)}")
            continue
        if action == "reset":
            current = World(problem.start.placement.copy())
            show_world("Reset to start", current)
            continue
        if action == "move" and len(command) == 3:
            try:
                move = Move(moving=int(command[1]), destination=int(command[2]))
                current.update(move)
            except (ValueError, AssertionError, IndexError) as error:
                print(f"Move rejected: {error}")
                continue

            show_world("Current", current)
            if np.array_equal(current.placement, goal.placement):
                print("Goal reached!")
            continue

        print("Unknown command. Use: show, move <block_id> <destination_id>, reset, quit.")


if __name__ == "__main__":
    main()
