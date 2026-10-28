from packaging.version import Version

from package_manager.domain.model import State
from package_manager.use_cases.install_with_state import build_change_plan


def test_build_change_plan_covers_install_remove_upgrade_and_downgrade():
    initial = State(
        packages={
            "keep": (Version("1.0"), False),
            "remove-me": (Version("1.0"), False),
            "upgrade-me": (Version("1.0"), False),
            "downgrade-me": (Version("2.0"), False),
        }
    )
    final = State(
        packages={
            "keep": (Version("1.0"), False),
            "install-me": (Version("1.0"), False),
            "upgrade-me": (Version("2.0"), False),
            "downgrade-me": (Version("1.5"), False),
        }
    )

    assert build_change_plan(initial, final) == [
        "Downgrade downgrade-me 2.0 -> 1.5",
        "Install install-me 1.0",
        "Remove remove-me 1.0",
        "Upgrade upgrade-me 1.0 -> 2.0",
    ]


def test_build_change_plan_is_empty_when_states_match():
    state = State(packages={"keep": (Version("1.0"), False)})

    assert build_change_plan(state, state) == []
