import numpy as np

from .BlockState import BlockState



def state_generator(n_blocks:int, seed:int = 42) -> BlockState:
    np.random.seed(seed)

    path = []

    # Suggest Random Array till it match start conditions
    while True:
        start_prop = np.random.randint(0, n_blocks, size=n_blocks, dtype=np.int32)

        if BlockState._check_if_state_is_legal(start_prop):
            break

    start = start_prop
    

    # Random


    return BlockState(None, None)
