import z3

from package_manager.domain.model import State
from package_manager.domain.versioning import parse_version, normalize_package_name


def parse_state(text: str) -> State:
    state = {}
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue

        parts = line.split()
        name = normalize_package_name(parts[0])
        version = parse_version(parts[1])
        manual = len(parts) > 2 and parts[2] == "manual"

        state[name] = (version, manual)

    return State(packages=state)

def write_state(state: State) -> str:
    lines = []
    for package, (version, manual) in state.packages.items():
        lines.append(f"{package} {version}{" manual" if manual else ""}")

    return "\n".join(lines) + "\n" if lines else ""

def apply_state(opt, repo, variables, state):
    installed_keys = {(name, str(version)) for name, (version, _) in state.packages.items()}
    for package in repo.packages.values():
        for version in package.versions:
            key = (package.name, str(version))
            if key in installed_keys:
                opt.add(variables[key])
            else:
                opt.add(z3.Not(variables[key]))
