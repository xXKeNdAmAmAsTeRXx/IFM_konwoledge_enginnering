from typing import Iterable

from .errors import PackageError
from .model import Repository


def verify(repo: Repository, installed: Iterable[tuple[str, str]], requests=None) -> list[str]:
    # Installed are (package.name, package.version) given by install function (claimed to be installed)
    # TODO: check versions exist
    # TODO: check at most one version per package
    # TODO: check dependencies
    # TODO: check conflicts
    # TODO: check requests
    # TODO: return list of violation messages
    raise NotImplementedError