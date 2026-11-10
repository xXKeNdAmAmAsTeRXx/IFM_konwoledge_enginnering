from dataclasses import dataclass

@dataclass
class Observation:
    states: dict[str, str | None]

@dataclass
class Data:
    observations: list[Observation]
