"""Add a presentation camera/lights to an existing scene and render a preview."""

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

COLLECTION_NAME = "MVP_Render_Setup"


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def reset_render_collection():
    old = bpy.data.collections.get(COLLECTION_NAME)
    if old:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    collection = bpy.data.collections.new(COLLECTION_NAME)
    bpy.context.scene.collection.children.link(collection)
    return collection


def link_only(obj, collection):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    collection.objects.link(obj)


def add_area_light(collection, name, location, energy, size, color, target=(0, 0, 1)):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    point_at(obj, target)
    return obj


def add_strip_light(collection, name, location, rotation, energy, size, size_y, color):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.shape, data.size, data.size_y, data.color = energy, "RECTANGLE", size, size_y, color
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = [math.radians(value) for value in rotation]
    return obj


def setup(output, save_path):
    scene = bpy.context.scene
    collection = reset_render_collection()

    camera_data = bpy.data.cameras.new("MVP_Render_Camera")
    camera = bpy.data.objects.new("MVP_Render_Camera", camera_data)
    collection.objects.link(camera)
    camera.location = (11.5, -13.5, 9.2)
    camera_data.lens = 48
    point_at(camera, (0, 0.25, 1.15))
    scene.camera = camera

    add_area_light(collection, "Key_Light", (1.5, -2.5, 9), 1800, 6.0, (1.0, 0.82, 0.66))
    add_area_light(collection, "Fill_Light", (-7, -4, 5), 1100, 5.0, (0.55, 0.72, 1.0))
    add_area_light(collection, "Back_Light", (3, 5, 7), 1500, 4.0, (0.65, 0.82, 1.0), (0, 1, 1.4))
    # Narrow sources create readable reflection bands on dark painted metal.
    add_strip_light(collection, "Metal_Strip_Left", (-5.5, -1.5, 4.2), (58, 0, -32), 1050, 5.5, 0.22, (0.45, 0.68, 1.0))
    add_strip_light(collection, "Metal_Strip_Right", (5.5, -0.5, 4.8), (62, 0, 148), 1250, 5.0, 0.18, (1.0, 0.55, 0.25))

    world = scene.world or bpy.data.worlds.new("MVP_World")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.018, 0.025, 0.045, 1)
    background.inputs["Strength"].default_value = 0.28

    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.filepath = str(output.resolve())
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.resolution_percentage = 100

    bpy.ops.wm.save_as_mainfile(filepath=str(save_path.resolve()))
    bpy.ops.render.render(write_still=True)
    print(f"MVP_RENDER_OK output={output.resolve()} camera={camera.location[:]}")


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--save", required=True, type=Path)
    args = parser.parse_args(tail)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.save.parent.mkdir(parents=True, exist_ok=True)
    setup(args.output, args.save)


if __name__ == "__main__":
    main()
