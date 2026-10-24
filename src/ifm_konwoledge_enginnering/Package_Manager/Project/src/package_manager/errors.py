class PackageError(Exception):
    """Base error for package manager data problems."""

    def __init__(self, path: str = "", message: str = ""):
        self.path = path
        self.message = message
        super().__init__(str(self))

    def __str__(self) -> str:
        if self.path and self.message:
            return f"{self.path}: {self.message}"
        return self.message or self.path


class RepoError(PackageError):
    """An error in a repository JSON file."""


class RequestError(PackageError):
    """An error in a request/state file."""
