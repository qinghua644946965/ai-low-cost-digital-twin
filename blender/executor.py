"""Blender-side executor. Run only inside Blender's bundled Python."""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy

COLLECTION_NAME = "DigitalTwinMVP"


def reset_managed_collection():
    previous = bpy.data.collections.get(COLLECTION_NAME)
    if previous:
        for obj in list(previous.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(previous)
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj, collection):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def apply_material(obj, color, settings=None):
    settings = settings or {}
    name = f"MVP_{obj.name}"
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    shader = material.node_tree.nodes["Principled BSDF"]
    shader.inputs["Base Color"].default_value = color
    shader.inputs["Metallic"].default_value = settings.get("metallic", 0.0)
    shader.inputs["Roughness"].default_value = settings.get("roughness", 0.5)
    emission_color = settings.get("emission_color")
    if emission_color and shader.inputs.get("Emission Color"):
        shader.inputs["Emission Color"].default_value = emission_color
    if shader.inputs.get("Emission Strength"):
        shader.inputs["Emission Strength"].default_value = settings.get("emission_strength", 0.0)
    obj.data.materials.clear()
    obj.data.materials.append(material)


def create(command, collection):
    primitive = command["primitive"]
    if primitive == "box":
        bpy.ops.mesh.primitive_cube_add(size=1, location=command["position"])
    elif primitive == "cylinder":
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=command["radius"], depth=command["depth"], location=command["position"])
    elif primitive == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=command["radius"], location=command["position"])
    else:
        raise ValueError(f"unsupported primitive: {primitive}")
    obj = bpy.context.object
    obj.name = command["id"]
    obj["digital_twin_id"], obj["primitive"] = command["id"], primitive
    if "metadata" in command:
        obj["digital_twin_metadata"] = json.dumps(command["metadata"], ensure_ascii=False)
    if primitive == "box":
        obj.dimensions = command["dimensions"]
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.rotation_euler = [math.radians(value) for value in command["rotation_deg"]]
    settings = command.get("material") or {}
    bevel_width = settings.get("bevel_width", 0.0)
    if primitive == "box" and bevel_width > 0:
        bevel = obj.modifiers.new("MVP_Edge_Bevel", "BEVEL")
        bevel.width = bevel_width
        bevel.segments = 3
    if primitive in ("cylinder", "sphere"):
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    apply_material(obj, command["color"], settings)
    move_to_collection(obj, collection)
    return obj


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def execute(program, output_path, clear_existing=False):
    if program.get("ir_version") != "0.1":
        raise ValueError("unsupported IR version")
    if clear_existing:
        clear_scene()
    collection, created, by_id = reset_managed_collection(), [], {}
    for command in program.get("commands", []):
        if command.get("op") != "CREATE_PRIMITIVE":
            raise ValueError(f"unsupported operation: {command.get('op')}")
        obj = create(command, collection)
        created.append(obj)
        by_id[command["id"]] = obj
    for command in program.get("commands", []):
        parent_id = command.get("parent_id")
        if parent_id:
            obj = by_id[command["id"]]
            world = obj.matrix_world.copy()
            obj.parent = by_id[parent_id]
            obj.matrix_world = world
    bpy.context.scene["digital_twin_scene"] = program.get("scene_name", "Untitled scene")
    bpy.context.scene["digital_twin_ir_version"] = program["ir_version"]
    bpy.ops.wm.save_as_mainfile(filepath=str(output_path))
    print(f"MVP_EXECUTOR_OK objects={len(created)} output={output_path}")


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--clear-scene", action="store_true")
    args = parser.parse_args(tail)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    execute(json.loads(args.input.read_text(encoding="utf-8")), args.output.resolve(), args.clear_scene)


if __name__ == "__main__":
    main()
