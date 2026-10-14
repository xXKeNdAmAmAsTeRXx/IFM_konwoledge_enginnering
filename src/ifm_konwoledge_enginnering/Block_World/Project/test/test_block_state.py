from ifm_konwoledge_enginnering.Block_World.Project.src.BlockState import BlockState
from ifm_konwoledge_enginnering.Block_World.Project.src.Move import Move


def test_block_state_defaults():
    state = BlockState()

    assert state.id == -1
    assert state.clear is False
    assert state.on == 0
    assert state.on_table is False


def test_moving_block_updates_its_support_and_table_status():
    state = BlockState(id=2, clear=True, on=1, on_table=False)

    state.update(Move(moving=2, destination=0))

    assert state.on == 0
    assert state.on_table is True
    assert state.clear is True


def test_destination_block_becomes_not_clear():
    state = BlockState(id=3, clear=True, on=0, on_table=True)

    state.update(Move(moving=1, destination=3))

    assert state.clear is False
    assert state.on == 0
    assert state.on_table is True
