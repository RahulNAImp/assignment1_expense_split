"""Domain errors mapped to the exit codes fixed by the constitution (FR-013)."""


class SplitKaroError(Exception):
    exit_code = 1


class ValidationError(SplitKaroError):
    exit_code = 1


class NotFoundError(SplitKaroError):
    exit_code = 3


class ConflictError(SplitKaroError):
    exit_code = 4


class StorageError(SplitKaroError):
    exit_code = 5
