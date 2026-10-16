import numpy as np
from ..World import World



class LoadStartAndGoal:
    """
    Load the initial and target block arrangements.

    Attributes:
        start: World representing the initial arrangement.
        goal: World representing the target arrangement.
    """

    @staticmethod
    def load_from_txt(path:str):
        """Load start and goal layouts from a two-line text file.

        Blank lines and comment lines beginning with ``#`` are ignored.

        Returns the parsed layouts as start and goal World objects.
        """

        # utf-8-sig also copes with a BOM added by some Windows editors
        with open(path, "r", encoding="utf-8-sig") as f:
            lines = [line.strip() for line in f]

        layouts = [line for line in lines if line and not line.startswith("#")]
        if len(layouts) != 2:
            raise ValueError(
                f"{path}: expected 2 layout lines (start and target), "
                f"found {len(layouts)}"
            )

        parsed = []
        for name, line in zip(("start", "target"), layouts):
            try:
                parsed.append([int(token) for token in line.split()])
            except ValueError:
                raise ValueError(
                    f"{path}: {name} layout must contain only integers, got {line!r}"
                ) from None

        start, goal = np.array(parsed)
        print(start)
        state = LoadStartAndGoal(start, goal)

        return state


    def __init__(self, start:np.ndarray[np.int32] | World, goal:np.ndarray[np.int32] | World):
        """Create start and goal worlds from their placement arrays."""
        assert len(start) == len(goal)
        self.start = start if isinstance(start, World) else World(start)
        self.goal = goal if isinstance(goal, World) else World(goal)
