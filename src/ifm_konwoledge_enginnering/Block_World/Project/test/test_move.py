from ifm_konwoledge_enginnering.Block_World.Project.src.Move import Move


def test_move_stores_moving_block_and_destination():
    move = Move(moving=2, destination=0)

    assert move.moving == 2
    assert move.destination == 0


def test_moves_with_same_fields_are_equal():
    assert Move(moving=1, destination=3) == Move(moving=1, destination=3)
