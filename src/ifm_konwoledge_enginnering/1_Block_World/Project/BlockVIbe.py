import numpy as np


class BlockVIbe:
    """
    state: is a array defining a blocks array

    """
    def _check_if_state_is_legal(self, state:np.ndarray[np.uint32]) -> bool:

        assert (state == 0).any(), "Any Block must be on table"
        assert (state != (state.__index__() + 1)).all(), "Block cannot be on itself"
        assert (np.unique(state[state!=0]) == len(state)).all(), "More then one block cannot be placed on same block"
        #TODO: Check and add rest

        pass

    def __init__(self, state: np.ndarray[np.uint32])
        pass