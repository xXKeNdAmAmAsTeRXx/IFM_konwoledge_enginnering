from typing import Iterable

from package_manager.domain.model import Repository
from package_manager.domain.versioning import parse_requirement, parse_version


def verify(repo: Repository, installed: Iterable[tuple[str, str]], requests=None) -> list[str]:
    # Installed are (package.name, package.version) given by install function (claimed to be installed)
    packages_appearance = {}
    errors = []
    for package_name, version in installed:

        # Check if package exist - skip other checks if package is not real
        if not repo.has_package(package_name):
            errors.append(f"Package {package_name} do not exist")
            continue

        package = repo.packages[package_name]
        version = parse_version(version)

        # Check if version exist - if not no point in checking requirements and conflicts
        if not version in repo.versions_of(package_name):
            errors.append(f"Package {package_name} version {version} do not exist")
            continue

        # Check if package is doubled
        if packages_appearance.get(package_name, None) is not None:
            errors.append(f"Package {package_name} already installed")
        else:
            packages_appearance[package_name] = version


        # get package version info
        version_info = package.versions[version]


        # Check conflicts
        conflits = version_info.conflicts
        for req in conflits:
            for atom in req.alternatives:
                for other_version in repo.versions_of(atom.package):
                    if atom.matches_version(other_version):
                        other_key = (atom.package, str(other_version))
                        if other_key in installed:
                            errors.append(f"Package {package_name}={version} conflict with {atom.package}={str(other_version)}")


        # Check requests
        requires = version_info.requires
        installed_versions = {p: parse_version(v) for p, v in installed}

        for req in requires:
            satisfied = False
            for atom in req.alternatives:
                if atom.package in installed_versions:
                    other_version = installed_versions[atom.package]
                    if atom.matches_version(other_version):
                        satisfied = True
                        break
            if not satisfied:
                errors.append(f"Package {package_name}={version} requires {req}")

    # Verify Request
    if requests:
        installed_map = {p: parse_version(v) for p, v in installed}
        for req_str in requests:
            req = parse_requirement(req_str)
            satisfied = any(
                atom.package in installed_map
                and atom.matches_version(installed_map[atom.package])
                for atom in req.alternatives
            )
            if not satisfied:
                errors.append(f"unmet request: {req_str}")

    return errors
