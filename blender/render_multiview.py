"""Render a scene from repeatable inspection viewpoints for semantic refinement."""

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


VIEWS = {
    "front_left": (-11.5, -13.5, 7.2),
    "front_right": (11.5, -13.5, 7.2),
    "rear_left": (-11.5, 12.5, 7.0),
    "rear_right": (11.5, 12.5, 7.0),
    "top": (0.0, 0.0, 18.0),
}


def point_at(obj, target, up="Y"):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", up).to_euler()


def ensure_camera():
    camera = bpy.data.objects.get("MVP_Multiview_Camera")
    if camera is None:
        data = bpy.data.cameras.new("MVP_Multiview_Camera")
        camera = bpy.data.objects.new("MVP_Multiview_Camera", data)
        bpy.context.scene.collection.objects.link(camera)
    camera.data.lens = 50
    bpy.context.scene.camera = camera
    return camera


def setup_world_and_lights():
    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("MVP_Multiview_World")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.025, 0.035, 0.06, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.38
    if bpy.data.objects.get("MVP_Multiview_Key") is None:
        data = bpy.data.lights.new("MVP_Multiview_Key", "AREA")
        data.energy, data.shape, data.size = 2200, "DISK", 7
        key = bpy.data.objects.new("MVP_Multiview_Key", data)
        scene.collection.objects.link(key)
        key.location = (0, 0, 10)
        point_at(key, (0, 0, 0))


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(tail)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = 960, 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    setup_world_and_lights()
    camera = ensure_camera()

    for name, location in VIEWS.items():
        camera.location = location
        point_at(camera, (0, 0.25, 1.15), "Y" if name != "top" else "Y")
        scene.render.filepath = str((args.output_dir / f"{name}.png").resolve())
        bpy.ops.render.render(write_still=True)
        print(f"MVP_MULTIVIEW_OK view={name} output={scene.render.filepath}")


if __name__ == "__main__":
    main()
