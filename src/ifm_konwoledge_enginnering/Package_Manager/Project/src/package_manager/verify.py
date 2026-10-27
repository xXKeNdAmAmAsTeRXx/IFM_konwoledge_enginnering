from typing import Iterable

from .errors import PackageError
from .model import Repository
from .parsing import parse_version


def verify(repo: Repository, installed: Iterable[tuple[str, str]], requests=None) -> list[str]:
    # Installed are (package.name, package.version) given by install function (claimed to be installed)

    errors = []
    for package_name, version in installed:

        # Check if package exist
        if not repo.has_package(package_name):
            errors.append(f"Package {package_name} do not exist")

        package = repo.packages[package_name]
        version = parse_version(version)

        # Check if version exist
        if not version in repo.versions_of(package_name):
            errors.append(f"Package {package_name} version {version} do not exist")

        # get package version info
        version_info = package.versions[version]

        # Check conflicts
        conflits = version_info.conflicts


        # Check requests
        requests = version_info.requests

    # TODO: check versions exist
    # TODO: check at most one version per package
    # TODO: check dependencies
    # TODO: check conflicts
    # TODO: check requests
    # TODO: return list of violation messages

    return errors
    raise NotImplementedError