from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from packaging.version import Version

@dataclass(frozen=True)
class Constraint:
    op: str
    version: Version

    _OPS = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
    }
    def matches(self, version: Version) -> bool:
        if self.op not in self._OPS:
            raise ValueError(f"Invalid constraint {self.op}")
        return self._OPS[self.op](version, self.version)


@dataclass
class Atom:
    package: str
    constraints: List[Constraint] = field(default_factory=list)


    def matches_version(self, version: Version) -> bool:
        for constraint in self.constraints:
            if not constraint.matches(version):
                return False

        return True

@dataclass
class Requirement:
    alternatives: List[Atom]

    def is_satisfiable(self, repo: Repository) -> bool:
        for atom in self.alternatives:
            if not repo.has_package(atom.package):
                continue

            versions = repo.versions_of(atom.package)
            if any(atom.matches_version(v) for v in versions):
                return True
        return False

@dataclass
class VersionInfo:
    requires: List[Requirement] = field(default_factory=list)
    conflicts: List[Requirement] = field(default_factory=list)


@dataclass
class Package:
    name: str
    versions: Dict[Version, VersionInfo] = field(default_factory=dict)


@dataclass
class Repository:
    packages: Dict[str, Package] = field(default_factory=dict)
    meta: Any = None

    def has_package(self, name: str) -> bool:
        return name in self.packages

    def versions_of(self, name: str) -> List[Version]:
        if not self.has_package(name):
            return []

        return sorted(list(self.packages[name].versions.keys()), reverse=True)