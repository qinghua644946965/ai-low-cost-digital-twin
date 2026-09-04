"""Generate a larger flat semantic JSON scene without using an AI service."""

import json
from pathlib import Path


def box(object_id, dimensions, position, color, **extra):
    return {"id": object_id, "primitive": "box", "dimensions": dimensions,
            "position": position, "color": color, **extra}


def sphere(object_id, radius, position, color):
    return {"id": object_id, "primitive": "sphere", "radius": radius,
            "position": position, "color": color}


def cylinder(object_id, radius, depth, position, color, rotation_deg=None):
    result = {"id": object_id, "primitive": "cylinder", "radius": radius,
              "depth": depth, "position": position, "color": color}
    if rotation_deg:
        result["rotation_deg"] = rotation_deg
    return result


objects = [
    box("floor", [10, 7, 0.12], [0, 0, -0.06], [0.1, 0.12, 0.15, 1]),
    box("back_wall", [10, 0.12, 3.4], [0, 3.5, 1.7], [0.52, 0.55, 0.59, 1]),
    box("left_wall", [0.12, 7, 3.4], [-5, 0, 1.7], [0.43, 0.46, 0.5, 1]),
    box("right_wall", [0.12, 7, 3.4], [5, 0, 1.7], [0.43, 0.46, 0.5, 1]),
    box("cold_aisle", [7.2, 1.15, 0.025], [0, 0, 0.015], [0.02, 0.25, 0.58, 1]),
    box("hot_aisle_back", [7.2, 0.55, 0.025], [0, 2.35, 0.015], [0.55, 0.08, 0.03, 1]),
    box("hot_aisle_front", [7.2, 0.55, 0.025], [0, -2.35, 0.015], [0.55, 0.08, 0.03, 1]),
]

# Eight rack cabinets, each with a door frame, four device layers and one status beacon.
rack_x = [-3.0, -1.0, 1.0, 3.0]
for row_name, rack_y, front_y, panel_y in (("a", 1.35, 0.81, 0.795), ("b", -1.35, -0.81, -0.795)):
    for index, x in enumerate(rack_x, 1):
        rack_id = f"rack_{row_name}{index}"
        objects.append(box(rack_id, [0.82, 1.02, 2.25], [x, rack_y, 1.125], [0.025, 0.03, 0.045, 1]))
        objects.append(box(f"{rack_id}_door", [0.72, 0.035, 2.08], [x, front_y, 1.125], [0.08, 0.1, 0.13, 1]))
        for unit, z in enumerate((0.48, 0.82, 1.16, 1.50), 1):
            if row_name == "b" and index == 3 and unit == 3:
                color = [0.78, 0.055, 0.025, 1]
            elif unit == 4:
                color = [0.12, 0.42, 0.75, 1]
            else:
                color = [0.16, 0.2, 0.25, 1]
            objects.append(box(f"server_{row_name}{index}_u{unit}", [0.63, 0.055, 0.22], [x, panel_y, z], color))
        status_color = [1, 0.08, 0.025, 1] if row_name == "b" and index == 3 else [0.08, 1, 0.18, 1]
        objects.append(sphere(f"status_{row_name}{index}", 0.06, [x, panel_y - 0.04 if row_name == "a" else panel_y + 0.04, 1.91], status_color))

# Cooling equipment and visible outlet grilles.
for side, x in (("left", -4.25), ("right", 4.25)):
    objects.append(box(f"cooling_{side}", [1.0, 0.8, 2.35], [x, 2.75, 1.175], [0.72, 0.77, 0.82, 1]))
    for grille in range(3):
        objects.append(box(f"cooling_{side}_vent_{grille+1}", [0.72, 0.035, 0.12], [x, 2.33, 1.55 + grille * 0.23], [0.12, 0.16, 0.2, 1]))

# Entrance, overhead cable trays and ceiling lights.
objects.extend([
    box("door_left_frame", [0.12, 0.35, 2.5], [-0.76, 3.28, 1.25], [0.1, 0.12, 0.14, 1]),
    box("door_right_frame", [0.12, 0.35, 2.5], [0.76, 3.28, 1.25], [0.1, 0.12, 0.14, 1]),
    box("door_top_frame", [1.64, 0.35, 0.12], [0, 3.28, 2.46], [0.1, 0.12, 0.14, 1]),
    box("door", [1.35, 0.08, 2.3], [0, 3.2, 1.15], [0.24, 0.3, 0.36, 1]),
    cylinder("door_handle", 0.055, 0.12, [0.48, 3.12, 1.15], [0.9, 0.65, 0.12, 1], [90, 0, 0]),
    box("cable_tray_left", [0.32, 5.3, 0.16], [-2.0, 0, 2.85], [0.34, 0.36, 0.38, 1]),
    box("cable_tray_right", [0.32, 5.3, 0.16], [2.0, 0, 2.85], [0.34, 0.36, 0.38, 1]),
])
for index, y in enumerate((-2.3, -0.75, 0.75, 2.3), 1):
    objects.append(box(f"ceiling_light_{index}", [3.2, 0.16, 0.07], [0, y, 3.05], [1, 0.9, 0.55, 1]))
for index, x in enumerate((-3.4, -1.7, 0, 1.7, 3.4), 1):
    objects.append(cylinder(f"temperature_sensor_{index}", 0.1, 0.22, [x, 3.30, 2.45], [1, 0.55, 0.03, 1], [90, 0, 0]))

scene = {"schema_version": "0.1", "name": "Server room complexity level 2",
         "units": "meters", "objects": objects}
output = Path(__file__).with_name("server-room-l2.scene.json")
output.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
print(f"Generated {len(objects)} semantic objects -> {output}")
