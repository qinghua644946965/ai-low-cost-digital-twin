"""Enrich level 2 with asset semantics, hierarchy and facility details."""

import json
from pathlib import Path

folder = Path(__file__).parent
source = json.loads((folder / "server-room-l2.scene.json").read_text(encoding="utf-8"))
objects = source["objects"]

for obj in objects:
    object_id = obj["id"]
    metadata = {"source": "synthetic-mvp"}
    if object_id.startswith("rack_") and "_door" not in object_id:
        metadata.update({"asset_id": object_id.upper(), "asset_type": "rack", "zone": "server-room"})
    elif object_id.startswith("server_"):
        rack_id = "rack_" + object_id.split("_")[1]
        obj["parent_id"] = rack_id
        status = "alarm" if object_id == "server_b3_u3" else "online"
        metadata.update({"asset_id": object_id.upper(), "asset_type": "server", "rack_id": rack_id,
                         "rack_unit": object_id.split("_")[2], "status": status,
                         "temperature_c": 46.8 if status == "alarm" else 24.6})
    elif object_id.startswith("status_"):
        rack_id = "rack_" + object_id.split("_")[1]
        obj["parent_id"] = rack_id
        metadata.update({"asset_type": "status_beacon", "rack_id": rack_id})
    elif object_id.startswith("temperature_sensor_"):
        metadata.update({"asset_id": object_id.upper(), "asset_type": "temperature_sensor",
                         "status": "online", "temperature_c": 25.2})
    elif object_id.startswith("cooling_") and "vent" not in object_id:
        metadata.update({"asset_id": object_id.upper(), "asset_type": "precision_cooling",
                         "status": "online", "supply_temperature_c": 18.5})
    obj["metadata"] = metadata


def add_box(object_id, dimensions, position, color, metadata):
    objects.append({"id": object_id, "primitive": "box", "dimensions": dimensions,
                    "position": position, "color": color, "metadata": metadata})


def add_cylinder(object_id, radius, depth, position, rotation, color, metadata):
    objects.append({"id": object_id, "primitive": "cylinder", "radius": radius, "depth": depth,
                    "position": position, "rotation_deg": rotation, "color": color, "metadata": metadata})


# Individually addressable raised-floor tiles.
for row, y in enumerate((-2.8, -1.8, -0.6, 0.6, 1.8, 2.8), 1):
    for column, x in enumerate((-4.5, -3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5, 4.5), 1):
        add_box(f"floor_tile_{row}_{column}", [0.96, 0.96, 0.035], [x, y, 0.035],
                [0.17, 0.19, 0.22, 1], {"asset_type": "raised_floor_tile", "row": row, "column": column})

# Addressable facility systems.
for index, x in enumerate((-3, -1, 1, 3), 1):
    add_cylinder(f"power_bus_{index}", 0.045, 5.2, [x, 0, 3.02], [90, 0, 0],
                 [0.8, 0.18, 0.04, 1], {"asset_type": "power_bus", "voltage_v": 380})
for index, x in enumerate((-4.55, 4.55), 1):
    add_cylinder(f"cooling_pipe_{index}", 0.08, 5.4, [x, 0, 2.75], [90, 0, 0],
                 [0.05, 0.45, 0.9, 1], {"asset_type": "cooling_pipe", "status": "normal"})
for index, x in enumerate((-3.8, 3.8), 1):
    add_cylinder(f"camera_{index}", 0.13, 0.28, [x, 3.18, 2.75], [90, 0, 0],
                 [0.08, 0.09, 0.1, 1], {"asset_id": f"CAM-{index:02d}", "asset_type": "camera", "status": "online"})
add_cylinder("fire_extinguisher", 0.14, 0.62, [-4.55, -2.8, 0.31], [0, 0, 0],
             [0.9, 0.025, 0.015, 1], {"asset_id": "FIRE-01", "asset_type": "fire_extinguisher"})
add_box("control_console", [1.3, 0.62, 0.82], [4.0, -2.75, 0.41], [0.16, 0.2, 0.25, 1],
        {"asset_id": "CONSOLE-01", "asset_type": "control_console", "status": "online"})
add_box("console_screen", [0.75, 0.08, 0.46], [4.0, -2.42, 1.02], [0.02, 0.5, 0.82, 1],
        {"asset_type": "display", "parent_asset": "CONSOLE-01"})

source["name"] = "Server room complexity level 3 - operational semantics"

# Material intent remains semantic data; Blender translates it to shader inputs.
for obj in objects:
    object_id = obj["id"]
    material = {"roughness": 0.55, "metallic": 0.0}
    if object_id.startswith("rack_"):
        obj["color"] = [0.07, 0.09, 0.14, 1]
        material = {"roughness": 0.24, "metallic": 0.82, "bevel_width": 0.028}
    elif object_id.startswith("server_"):
        if object_id != "server_b3_u3":
            obj["color"] = [0.12, 0.16, 0.23, 1]
        material = {"roughness": 0.2, "metallic": 0.86, "bevel_width": 0.012}
    elif object_id.startswith("cable_tray"):
        material = {"roughness": 0.25, "metallic": 0.8, "bevel_width": 0.02}
    elif object_id.startswith(("power_bus_", "cooling_pipe_", "door_handle")):
        material = {"roughness": 0.14, "metallic": 0.94}
    elif object_id.startswith("floor_tile_"):
        material = {"roughness": 0.72, "metallic": 0.12, "bevel_width": 0.012}
    elif object_id in ("floor", "back_wall", "left_wall", "right_wall"):
        material = {"roughness": 0.92, "metallic": 0.0}
    elif object_id.startswith("status_"):
        material = {"roughness": 0.18, "metallic": 0.05,
                    "emission_color": obj["color"], "emission_strength": 5.0}
    elif object_id in ("console_screen",) or object_id.startswith("ceiling_light_"):
        material = {"roughness": 0.15, "metallic": 0.0,
                    "emission_color": obj["color"], "emission_strength": 3.0}
    elif object_id == "fire_extinguisher":
        material = {"roughness": 0.24, "metallic": 0.65}
    obj["material"] = material

output = folder / "server-room-l3.scene.json"
output.write_text(json.dumps(source, indent=2) + "\n", encoding="utf-8")
print(f"Generated {len(objects)} semantic objects -> {output}")
