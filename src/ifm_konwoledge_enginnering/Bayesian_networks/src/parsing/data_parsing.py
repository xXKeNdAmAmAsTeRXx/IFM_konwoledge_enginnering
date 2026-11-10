import csv
from typing import List

from models.data import Data, Observation
from models.variable import Variable


def _validate_header(path: str, header: List[str], variables_dict: dict[str, Variable]) -> None:
    if not header:
        raise ValueError(f"{path}:1: missing header")

    if any(not name for name in header):
        raise ValueError(f"{path}:1: empty column name")

    duplicates = sorted({name for name in header if header.count(name) > 1})
    if duplicates:
        raise ValueError(f"{path}:1: duplicate column(s): {', '.join(duplicates)}")

    unknown = sorted(set(header) - set(variables_dict))
    if unknown:
        raise ValueError(f"{path}:1: unknown column(s): {', '.join(unknown)}")

    missing = sorted(set(variables_dict) - set(header))
    if missing:
        raise ValueError(f"{path}:1: missing column(s): {', '.join(missing)}")


def parse_data(
    path: str,
    variables_dict: dict[str, Variable],
    allow_missing: bool = True,
) -> Data:
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)

        try:
            header_row = next(reader)
        except StopIteration:
            raise ValueError(f"{path}: missing header") from None

        header = [name.strip() for name in header_row]
        _validate_header(path, header, variables_dict)

        observations = []
        for line_number, row in enumerate(reader, start=2):
            if not row:
                raise ValueError(f"{path}:{line_number}: blank line")

            if len(row) != len(header):
                raise ValueError(
                    f"{path}:{line_number}: expected {len(header)} fields, "
                    f"got {len(row)}"
                )

            states = {}
            for name, raw_state in zip(header, row):
                state = raw_state.strip() or None

                if state is None:
                    if not allow_missing:
                        raise ValueError(
                            f"{path}:{line_number}: missing value for variable {name}"
                        )
                else:
                    variable = variables_dict[name]
                    if state not in variable.states:
                        raise ValueError(
                            f"{path}:{line_number}: unknown state {state!r} "
                            f"for variable {name}"
                        )

                states[name] = state

            observations.append(Observation(states=states))

    return Data(observations=observations)
