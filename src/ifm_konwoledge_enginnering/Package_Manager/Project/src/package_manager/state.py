import z3

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

def write_state(state: State) -> str:
    lines = []
    for package, (version, manual) in state.packages.items():
        lines.append(f"{package} {version}{" manual" if manual else ""}")

    return "\n".join(lines) + "\n" if lines else ""

def apply_state(opt, repo, variables, state):
    installed_keys = state.get_packages_list()
    for package in repo.packages.values():
        for version in package.versions:
            key = (package.name, str(version))
            if key in installed_keys:
                opt.add(variables[key])
            else:
                opt.add(z3.Not(variables[key]))
