"""The small instruction representation consumed by Blender."""

from dataclasses import asdict, dataclass
from typing import Any

SUPPORTED_PRIMITIVES = {"box", "cylinder", "sphere"}


@dataclass(frozen=True)
class CreatePrimitive:
    op: str
    id: str
    primitive: str
    position: list[float]
    rotation_deg: list[float]
    color: list[float]
    dimensions: list[float] | None = None
    radius: float | None = None
    depth: float | None = None
    parent_id: str | None = None
    metadata: dict[str, Any] | None = None
    material: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {key: value for key, value in asdict(self).items() if value is not None}


def make_program(scene_name: str, commands: list[CreatePrimitive]) -> dict[str, Any]:
    return {"ir_version": "0.1", "scene_name": scene_name, "units": "meters",
            "commands": [command.to_dict() for command in commands]}
