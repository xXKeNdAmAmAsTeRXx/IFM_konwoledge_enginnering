from package_manager.model import State
from package_manager.versioning import parse_version


def parse_state(text: str) -> State:
    state = {}
    for raw in text.splitlines():
        if raw[0] == "#" or not raw:
            continue

        line = raw.split(" ")
        name, version = line[:2]
        manual = True if line[-1] == "manual" else False

        state[name] = (parse_version(version), manual)

    return State(packages=state)

