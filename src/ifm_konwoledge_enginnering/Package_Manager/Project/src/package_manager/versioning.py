import re
from packaging.version import Version, InvalidVersion

from .errors import RepoError
from .model import Requirement, Constraint, Atom, Repository

PAUSE_SYMBOLS_REGEX = r"[-_.]+"
PACKAGE_REGEX = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*$')


def normalize_package_name(package_name:str) -> str:
    """
    normalizing package name to lowercase + '-' pause symbol + package name validation
    """

    global PAUSE_SYMBOLS_REGEX, PACKAGE_REGEX

    if not PACKAGE_REGEX.match(package_name):
        raise ValueError("Invalid package name")

    return re.sub(PAUSE_SYMBOLS_REGEX, "-", package_name).lower()

def parse_version(value:str) -> Version:

    if not isinstance(value, str) or not value.strip():
        raise ValueError("version must be not empty string")

    try:
         return Version(value)
    except InvalidVersion as e:
        raise ValueError(f"Invalid version {value}") from e

def parse_requirement(requirements: str, path: str = "") -> Requirement:
    if not isinstance(requirements, str) or not requirements.strip():
        raise RepoError(path, "requirement must be a non-empty string")

    alternatives_raw = [part.strip() for part in requirements.split("|")]
    if any(not part for part in alternatives_raw):
        raise RepoError(path, "empty alternative in requirement")

    atoms = []
    for alternative in alternatives_raw:
        text = alternative.replace(",", " ")

        name_match = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", text)
        if not name_match:
            raise RepoError(path, f"invalid requirement {requirements!r}")

        try:
            package_name = normalize_package_name(name_match.group(0))
        except ValueError as exc:
            raise RepoError(path, str(exc))

        rest = text[name_match.end():]

        constraints = []
        for match in re.finditer(r"(==|!=|<=|>=|<|>)\s*([^\s,]+)", rest):
            op = match.group(1)
            version_str = match.group(2)
            try:
                version = parse_version(version_str)
            except ValueError as exc:
                raise RepoError(path, str(exc))
            constraints.append(Constraint(op, version))

        cleaned = re.sub(r"(==|!=|<=|>=|<|>)\s*[^\s,]+", "", rest)
        if cleaned.strip():
            raise RepoError(path, f"invalid requirement syntax in {requirements!r}")

        atoms.append(Atom(package=package_name, constraints=constraints))

    return Requirement(alternatives=atoms)




def requirement_is_satisfiable(req: Requirement, repo: Repository) -> bool:
    for atom in req.alternatives:
        versions = repo.versions_of(atom.package)
        if any(atom.matches_version(v) for v in versions):
            return True
    return False


def find_unsatisfiable(repo: Repository):
    results = []
    for pkg_name, package in repo.packages.items():
        for version, info in package.versions.items():
            for i, req in enumerate(info.requires):
                if not requirement_is_satisfiable(req, repo):
                    results.append(
                        (
                            f"packages['{pkg_name}'].versions['{version}'].requires[{i}]",
                            f"requirement {req} matches no version in the repository",
                        )
                    )
            for i, req in enumerate(info.conflicts):
                if not requirement_is_satisfiable(req, repo):
                    results.append(
                        (
                            f"packages['{pkg_name}'].versions['{version}'].conflicts[{i}]",
                            f"conflict {req} matches no version in the repository",
                        )
                    )
    return results
