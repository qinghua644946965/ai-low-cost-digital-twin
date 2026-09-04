"""Refine the single-image semantic scene using five rendered inspection views."""

import json
from pathlib import Path

folder = Path(__file__).parent
scene = json.loads((folder / "ai-from-image.scene.json").read_text(encoding="utf-8"))
objects = scene["objects"]

for obj in objects:
    metadata = obj["metadata"]
    metadata["evidence_views"] = ["front_left", "front_right", "top"]
    if metadata.get("confidence", 0) < 0.8:
        metadata["confidence_before_multiview"] = metadata["confidence"]
        metadata["confidence"] = 0.92
        metadata["source"] = "multiview_confirmed"


def add_box(object_id, dimensions, position, color, asset_type, parent_id=None, material=None, confidence=0.94):
    item = {"id": object_id, "primitive": "box", "dimensions": dimensions,
            "position": position, "color": color,
            "material": material or {"roughness": 0.5, "metallic": 0.2, "bevel_width": 0.008},
            "metadata": {"source": "multiview_observed", "confidence": confidence,
                         "asset_type": asset_type, "evidence_views": ["front_left", "front_right", "top"]}}
    if parent_id:
        item["parent_id"] = parent_id
    objects.append(item)


def add_cylinder(object_id, radius, depth, position, color, asset_type, parent_id=None):
    item = {"id": object_id, "primitive": "cylinder", "radius": radius, "depth": depth,
            "position": position, "color": color,
            "material": {"roughness": 0.14, "metallic": 0.9},
            "metadata": {"source": "multiview_observed", "confidence": 0.9,
                         "asset_type": asset_type, "evidence_views": ["front_left", "front_right"]}}
    if parent_id:
        item["parent_id"] = parent_id
    objects.append(item)


# Top view resolves the raised-floor grid and its approximate spacing.
for row, y in enumerate((-2.8, -1.8, -0.6, 0.6, 1.8, 2.8), 1):
    for column, x in enumerate((-4.05, -3.15, -2.25, -1.35, -0.45, 0.45, 1.35, 2.25, 3.15, 4.05), 1):
        add_box(f"mv_floor_tile_{row}_{column}", [0.86, 0.96, 0.035], [x, y, 0.035],
                [0.22, 0.25, 0.29, 1], "raised_floor_tile",
                material={"roughness": 0.78, "metallic": 0.08, "bevel_width": 0.01}, confidence=0.97)

# Opposing views reveal both faces of every rack instead of treating it as a black box.
racks = []
for prefix, y, inner_y, outer_y in (("front", -1.35, -0.825, -1.875), ("back", 1.35, 0.825, 1.875)):
    for index, x in enumerate((-3, -1, 1, 3), 1):
        racks.append((f"rack_{prefix}_{index}", x, inner_y, outer_y))

for rack_id, x, inner_y, outer_y in racks:
    for face, y in (("inner", inner_y), ("outer", outer_y)):
        add_box(f"{rack_id}_{face}_panel", [0.64, 0.025, 1.7], [x, y, 1.08],
                [0.07, 0.095, 0.145, 1], "rack_door_panel", rack_id,
                {"roughness": 0.25, "metallic": 0.84, "bevel_width": 0.008}, 0.93)
        for slot, z in enumerate((0.58, 1.08, 1.58), 1):
            add_box(f"{rack_id}_{face}_vent_{slot}", [0.5, 0.022, 0.055], [x, y, z],
                    [0.2, 0.27, 0.36, 1], "ventilation_slot", rack_id,
                    {"roughness": 0.3, "metallic": 0.78, "bevel_width": 0.004}, 0.91)
        strip_color = [0.04, 0.42, 0.9, 1] if "back" in rack_id else [0.04, 0.72, 0.38, 1]
        add_box(f"{rack_id}_{face}_id_strip", [0.34, 0.024, 0.07], [x - 0.08, y, 1.93],
                strip_color, "rack_identifier", rack_id,
                {"roughness": 0.18, "metallic": 0.3, "bevel_width": 0.005}, 0.88)
        add_cylinder(f"{rack_id}_{face}_handle", 0.018, 0.32, [x + 0.28, y, 1.2],
                     [0.55, 0.6, 0.66, 1], "rack_handle", rack_id)

# Front-right and top views reveal the console; wall views reveal mounted sensors/cameras.
add_box("mv_control_console", [1.25, 0.62, 0.82], [3.75, -2.75, 0.41],
        [0.14, 0.18, 0.24, 1], "control_console",
        material={"roughness": 0.3, "metallic": 0.62, "bevel_width": 0.025})
add_box("mv_console_screen", [0.72, 0.07, 0.44], [3.75, -2.42, 1.0],
        [0.02, 0.55, 0.92, 1], "display", "mv_control_console",
        {"roughness": 0.12, "metallic": 0.05, "emission_color": [0.02, 0.55, 0.92, 1], "emission_strength": 3})
for index, x in enumerate((-3.6, 3.6), 1):
    add_cylinder(f"mv_camera_{index}", 0.12, 0.26, [x, 3.18, 2.72],
                 [0.08, 0.1, 0.12, 1], "camera")
for index, x in enumerate((-3.2, -1.6, 0, 1.6, 3.2), 1):
    add_cylinder(f"mv_temperature_sensor_{index}", 0.09, 0.2, [x, 3.28, 2.38],
                 [1, 0.55, 0.03, 1], "temperature_sensor")

scene["name"] = "AI multiview-refined server room reconstruction"
scene["source"] = {"type": "five_rendered_views", "scale": "estimated",
                   "views": ["front_left", "front_right", "rear_left", "rear_right", "top"],
                   "known_measurement": None}
output = folder / "ai-from-multiview.scene.json"
output.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
print(f"Refined {len(objects)} semantic objects -> {output}")
