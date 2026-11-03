"""Update installed packages (Task 8.1) and conflict analysis (Task 8.2)."""

import z3

from package_manager.domain.errors import (
    InvalidInitialStateError,
    NoSolutionError,
    RequestError,
)
from package_manager.domain.model import Repository, State
from package_manager.domain.verification import verify
from package_manager.domain.versioning import parse_version
from package_manager.infrastructure.solver.knowledge_base import build_knowledge_base
from package_manager.infrastructure.solver.objective_builders import (
    count_selected_packages,
    count_unselected_packages,
    count_version_changes,
    obsolescence_cost,
    package_selected,
)
from package_manager.use_cases.explain import explain


def _check_state(repo: Repository, state: State) -> None:
    errors = verify(repo, state.get_packages_list())
    if errors:
        raise InvalidInitialStateError("initial_state", "; ".join(errors))


def _targets(state: State, package_names) -> set[str]:
    """Packages to update. No names given = all installed packages."""
    installed = set(state.packages)
    if not package_names:
        return installed
    targets = set(package_names)
    unknown = targets - installed
    if unknown:
        raise RequestError("update", f"not installed: {', '.join(sorted(unknown))}")
    return targets


def _manual(state: State) -> set[str]:
    return {name for name, (_, manual) in state.packages.items() if manual}


def _ranks(repo: Repository):
    """(package, version, obsolescence rank) for every version; rank 0 = newest."""
    return [
        (name, str(version), rank)
        for name in repo.packages
        for rank, version in enumerate(repo.versions_of(name))
    ]


def update(repo: Repository, state: State, package_names=None) -> State:
    """Task 8.1: update the packages in P (default: all)."""
    _check_state(repo, state)

    installed = state.get_packages_list()
    installed_names = {name for name, _ in installed}
    targets = _targets(state, package_names)

    variables, opt, _ = build_knowledge_base(repo)

    # Hard constraints: manual packages and packages from P stay installed.
    for name in _manual(state) | targets:
        opt.add(package_selected(repo, variables, name))

    ranks = _ranks(repo)
    # 1. obsolescence of packages from P
    e1 = obsolescence_cost(repo, variables, [t for t in ranks if t[0] in targets])
    # 2. number of removed packages
    e2 = count_unselected_packages(repo, variables, installed_names)
    # 3. version changes of packages outside P
    e3 = count_version_changes(
        repo, variables, [(n, v) for n, v in installed if n not in targets]
    )
    # 4. number of new packages
    e4 = count_selected_packages(
        repo, variables, [n for n in repo.packages if n not in installed_names]
    )
    # 5. obsolescence of all packages
    e5 = obsolescence_cost(repo, variables, ranks)

    opt.set(priority="lex")
    for expr in (e1, e2, e3, e4, e5):
        opt.minimize(expr)

    if opt.check() != z3.sat:
        raise NoSolutionError("", "no solution for the update")

    model = opt.model()
    chosen = [key for key, var in variables.items() if z3.is_true(model.eval(var))]
    flags = {name: manual for name, (_, manual) in state.packages.items()}
    return State(
        packages={
            name: (parse_version(version), flags.get(name, False))
            for name, version in chosen
        }
    )


def best_versions(repo: Repository, state: State, targets) -> dict[str, str]:
    """Task 8.2: newest reachable version of each target, checked separately."""
    manual = _manual(state)
    ranks = _ranks(repo)
    best = {}
    for name in sorted(targets):
        variables, opt, _ = build_knowledge_base(repo)
        for required in manual | {name}:
            opt.add(package_selected(repo, variables, required))
        opt.minimize(obsolescence_cost(repo, variables, [t for t in ranks if t[0] == name]))
        if opt.check() != z3.sat:
            raise NoSolutionError("", f"cannot keep {name} installed")
        model = opt.model()
        for (pkg, version), var in variables.items():
            if pkg == name and z3.is_true(model.eval(var)):
                best[name] = version
    return best


def analyze_update(repo: Repository, state: State, package_names=None, max_front=50) -> dict:
    """Check whether all newest reachable versions fit together.

    Returns a dict with: best (name -> version), core (list of labels, empty if
    no conflict), conflict (packages involved) and front (Pareto front).
    """
    _check_state(repo, state)
    targets = _targets(state, package_names)
    best = best_versions(repo, state, targets)

    ordered = sorted(best.items())
    requests = [f"{name}=={version}" for name, version in ordered] + sorted(_manual(state))
    core = explain(repo, requests)
    if not core:
        return {"best": best, "core": [], "conflict": [], "front": []}

    # Which "name==version" requests are in the core? Labels look like "Request #3: a==2.0".
    conflict = [
        name
        for i, (name, _) in enumerate(ordered)
        if any(label.startswith(f"Request #{i + 1}:") for label in core)
    ] or [name for name, _ in ordered]

    variables, opt, _ = build_knowledge_base(repo)
    for name in _manual(state) | targets:
        opt.add(package_selected(repo, variables, name))
    opt.set(priority="pareto")
    ranks = _ranks(repo)
    for name in conflict:
        opt.minimize(obsolescence_cost(repo, variables, [t for t in ranks if t[0] == name]))

    front = []
    while len(front) < max_front and opt.check() == z3.sat:
        model = opt.model()
        solution = {
            pkg: version
            for (pkg, version), var in variables.items()
            if pkg in conflict and z3.is_true(model.eval(var))
        }
        if solution not in front:
            front.append(solution)

    return {"best": best, "core": core, "conflict": conflict, "front": front}