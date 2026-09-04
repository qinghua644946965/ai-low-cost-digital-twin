"""Compile spatial-semantic JSON into the deliberately tiny Blender IR."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .ir import SUPPORTED_PRIMITIVES, CreatePrimitive, make_program


class SceneValidationError(ValueError):
    pass


def _vector(value: Any, name: str, length: int, default: list[float] | None = None) -> list[float]:
    if value is None and default is not None:
        return default.copy()
    if not isinstance(value, list) or len(value) != length or not all(isinstance(v, (int, float)) for v in value):
        raise SceneValidationError(f"{name} must contain {length} numbers")
    return [float(v) for v in value]


def compile_scene(scene: dict[str, Any]) -> dict[str, Any]:
    if scene.get("schema_version") != "0.1":
        raise SceneValidationError("schema_version must be '0.1'")
    if scene.get("units", "meters") != "meters":
        raise SceneValidationError("the MVP currently supports only meters")
    objects = scene.get("objects")
    if not isinstance(objects, list) or not objects:
        raise SceneValidationError("objects must be a non-empty list")

    commands, seen = [], set()
    for index, item in enumerate(objects):
        if not isinstance(item, dict):
            raise SceneValidationError(f"objects[{index}] must be an object")
        object_id, primitive = item.get("id"), item.get("primitive")
        if not isinstance(object_id, str) or not object_id.strip():
            raise SceneValidationError(f"objects[{index}].id must be a non-empty string")
        if object_id in seen:
            raise SceneValidationError(f"duplicate object id: {object_id}")
        seen.add(object_id)
        if primitive not in SUPPORTED_PRIMITIVES:
            raise SceneValidationError(f"{object_id}: unsupported primitive {primitive!r}")

        dimensions = radius = depth = None
        if primitive == "box":
            dimensions = _vector(item.get("dimensions"), f"{object_id}.dimensions", 3)
            if any(value <= 0 for value in dimensions):
                raise SceneValidationError(f"{object_id}.dimensions must be positive")
        else:
            radius = item.get("radius")
            if not isinstance(radius, (int, float)) or radius <= 0:
                raise SceneValidationError(f"{object_id}.radius must be positive")
            radius = float(radius)
            if primitive == "cylinder":
                depth = item.get("depth")
                if not isinstance(depth, (int, float)) or depth <= 0:
                    raise SceneValidationError(f"{object_id}.depth must be positive")
                depth = float(depth)

        color = _vector(item.get("color"), f"{object_id}.color", 4, [0.7, 0.7, 0.7, 1.0])
        if any(value < 0 or value > 1 for value in color):
            raise SceneValidationError(f"{object_id}.color values must be between 0 and 1")
        commands.append(CreatePrimitive(
            op="CREATE_PRIMITIVE", id=object_id, primitive=primitive,
            position=_vector(item.get("position"), f"{object_id}.position", 3, [0, 0, 0]),
            rotation_deg=_vector(item.get("rotation_deg"), f"{object_id}.rotation_deg", 3, [0, 0, 0]),
            color=color, dimensions=dimensions, radius=radius, depth=depth,
            parent_id=item.get("parent_id"), metadata=item.get("metadata"),
            material=item.get("material")))
    for command in commands:
        if command.parent_id is not None and command.parent_id not in seen:
            raise SceneValidationError(f"{command.id}: unknown parent_id {command.parent_id!r}")
        if command.metadata is not None and not isinstance(command.metadata, dict):
            raise SceneValidationError(f"{command.id}.metadata must be an object")
        if command.material is not None and not isinstance(command.material, dict):
            raise SceneValidationError(f"{command.id}.material must be an object")
        if command.material:
            for key in ("metallic", "roughness", "emission_strength"):
                value = command.material.get(key)
                if value is not None and (not isinstance(value, (int, float)) or value < 0):
                    raise SceneValidationError(f"{command.id}.material.{key} must be non-negative")
    return make_program(str(scene.get("name", "Untitled scene")), commands)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile spatial scene JSON to Blender MVP IR")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        program = compile_scene(json.loads(args.input.read_text(encoding="utf-8")))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(program, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    except (OSError, json.JSONDecodeError, SceneValidationError) as exc:
        print(f"compile error: {exc}", file=sys.stderr)
        return 1
    print(f"Compiled {len(program['commands'])} objects -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
