"""Parsing and validation for repository and request files."""

from __future__ import annotations

import json
from typing import List

from package_manager.domain.errors import RepoError
from package_manager.domain.model import Package, Repository, VersionInfo
from package_manager.domain.versioning import (
    normalize_package_name,
    parse_version,
    parse_requirement,
    find_unsatisfiable,
)


def _hook(pairs):
    seen = set()
    for key, _ in pairs:
        if key in seen:
            raise RepoError("", f"duplicate key {key!r}")
        seen.add(key)
    return dict(pairs)


def parse_repository_text(text: str, source: str = "<input>") -> Repository:
    try:
        data = json.loads(text, object_pairs_hook=_hook)
    except json.JSONDecodeError as exc:
        raise RepoError(source, f"JSON syntax error at line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except RepoError as exc:
        raise RepoError(source, exc.message)

    if not isinstance(data, dict):
        raise RepoError(source, "top-level value must be an object")

    unknown_top = set(data) - {"packages", "meta"}
    if unknown_top:
        key = sorted(unknown_top)[0]
        raise RepoError("root", f"unknown field {key!r}")
    if "packages" not in data:
        raise RepoError("root", "missing required field 'packages'")

    packages_raw = data["packages"]
    if not isinstance(packages_raw, dict):
        raise RepoError("packages", "must be an object")

    repo_packages = {}
    canonical_seen = set()

    for raw_name, raw_pkg in packages_raw.items():
        pkg_path = f"packages['{raw_name}']"

        try:
            canonical = normalize_package_name(raw_name)
        except ValueError as exc:
            raise RepoError(pkg_path, str(exc))

        if canonical in canonical_seen:
            raise RepoError(pkg_path, f"duplicate package {canonical!r}")
        canonical_seen.add(canonical)

        if not isinstance(raw_pkg, dict):
            raise RepoError(pkg_path, "must be an object")

        unknown_pkg = set(raw_pkg) - {"versions"}
        if unknown_pkg:
            key = sorted(unknown_pkg)[0]
            raise RepoError(pkg_path, f"unknown field {key!r}")
        if "versions" not in raw_pkg:
            raise RepoError(pkg_path, "missing required field 'versions'")

        versions_raw = raw_pkg["versions"]
        if not isinstance(versions_raw, dict):
            raise RepoError(f"{pkg_path}.versions", "must be an object")

        package = Package(name=canonical, versions={})

        for raw_ver, raw_info in versions_raw.items():
            ver_path = f"{pkg_path}.versions['{raw_ver}']"

            try:
                version = parse_version(raw_ver)
            except ValueError as exc:
                raise RepoError(ver_path, str(exc))

            if version in package.versions:
                raise RepoError(ver_path, f"duplicate version {version!r}")

            if not isinstance(raw_info, dict):
                raise RepoError(ver_path, "must be an object")

            unknown_info = set(raw_info) - {"requires", "conflicts"}
            if unknown_info:
                key = sorted(unknown_info)[0]
                raise RepoError(ver_path, f"unknown field {key!r}")

            requires_raw = raw_info.get("requires", [])
            conflicts_raw = raw_info.get("conflicts", [])

            if not isinstance(requires_raw, list) or not all(isinstance(x, str) for x in requires_raw):
                raise RepoError(f"{ver_path}.requires", "must be a list of strings")
            if not isinstance(conflicts_raw, list) or not all(isinstance(x, str) for x in conflicts_raw):
                raise RepoError(f"{ver_path}.conflicts", "must be a list of strings")

            requires = []
            for i, item in enumerate(requires_raw):
                req_path = f"{ver_path}.requires[{i}]"
                req = parse_requirement(item, req_path)
                for atom in req.alternatives:
                    if atom.package == canonical:
                        raise RepoError(req_path, "package cannot require itself")
                requires.append(req)

            conflicts = []
            for i, item in enumerate(conflicts_raw):
                conf_path = f"{ver_path}.conflicts[{i}]"
                if "|" in item:
                    raise RepoError(conf_path, "conflict cannot contain alternatives")
                req = parse_requirement(item, conf_path)
                if len(req.alternatives) != 1:
                    raise RepoError(conf_path, "conflict must be a single requirement")
                for atom in req.alternatives:
                    if atom.package == canonical:
                        raise RepoError(conf_path, "package cannot conflict with itself")
                conflicts.append(req)

            package.versions[version] = VersionInfo(requires=requires, conflicts=conflicts)

        repo_packages[canonical] = package

    return Repository(packages=repo_packages, meta=data.get("meta"))


def validate_repository(repo: Repository) -> list:
    """Print and return warnings for requirements that match no version."""
    warnings = find_unsatisfiable(repo)
    for path, message in warnings:
        print(f"WARNING {path}: {message}")
    return warnings


def load_repository(path: str) -> Repository:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    repo = parse_repository_text(text, source=path)
    validate_repository(repo)
    return repo


def parse_requests_text(text: str, source: str = "<input>") -> List[str]:
    requests = []
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if line:
            requests.append(line)
    return requests
