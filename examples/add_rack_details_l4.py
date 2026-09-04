"""Add visible front/rear rack construction to the level-3 semantic scene."""

import json
from pathlib import Path

folder = Path(__file__).parent
scene = json.loads((folder / "server-room-l3.scene.json").read_text(encoding="utf-8"))
objects = scene["objects"]


def box(object_id, dimensions, position, color, parent_id, material, metadata):
    objects.append({"id": object_id, "primitive": "box", "dimensions": dimensions,
                    "position": position, "color": color, "parent_id": parent_id,
                    "material": material, "metadata": metadata})


def cylinder(object_id, radius, depth, position, color, parent_id, material):
    objects.append({"id": object_id, "primitive": "cylinder", "radius": radius, "depth": depth,
                    "position": position, "color": color, "parent_id": parent_id,
                    "material": material,
                    "metadata": {"asset_type": "rack_handle", "rack_id": parent_id}})


rack_x = [-3.0, -1.0, 1.0, 3.0]
for row_name, rack_y, aisle_face_y, rear_face_y in (
        ("a", 1.35, 0.825, 1.875),
        ("b", -1.35, -0.825, -1.875)):
    for index, x in enumerate(rack_x, 1):
        rack_id = f"rack_{row_name}{index}"
        dark_metal = {"roughness": 0.26, "metallic": 0.84, "bevel_width": 0.009}
        frame_metal = {"roughness": 0.18, "metallic": 0.92, "bevel_width": 0.008}
        grille_metal = {"roughness": 0.34, "metallic": 0.76, "bevel_width": 0.004}

        # Vertical door frames remain visible from both aisle and rear views.
        for face_name, y in (("front", aisle_face_y), ("rear", rear_face_y)):
            for side_name, dx in (("left", -0.36), ("right", 0.36)):
                box(f"{rack_id}_{face_name}_frame_{side_name}", [0.045, 0.035, 2.06],
                    [x + dx, y, 1.12], [0.2, 0.24, 0.31, 1], rack_id, frame_metal,
                    {"asset_type": "rack_door_frame", "rack_id": rack_id, "face": face_name})

            # A recessed panel gives the black cabinet a readable surface plane.
            box(f"{rack_id}_{face_name}_panel", [0.63, 0.028, 1.72], [x, y, 1.08],
                [0.055, 0.075, 0.115, 1], rack_id, dark_metal,
                {"asset_type": "rack_door_panel", "rack_id": rack_id, "face": face_name})

            # Horizontal grille bars approximate perforated ventilation at primitive-only cost.
            for slot, z in enumerate((0.42, 0.64, 0.86, 1.08, 1.30, 1.52, 1.74), 1):
                box(f"{rack_id}_{face_name}_vent_{slot}", [0.52, 0.022, 0.055],
                    [x, y - 0.018 if face_name == "front" else y + 0.018, z],
                    [0.19, 0.25, 0.34, 1], rack_id, grille_metal,
                    {"asset_type": "ventilation_slot", "rack_id": rack_id, "face": face_name})

            # Vertical handle and a small colored identification strip.
            handle_y = y - 0.035 if face_name == "front" else y + 0.035
            cylinder(f"{rack_id}_{face_name}_handle", 0.018, 0.34,
                     [x + 0.285, handle_y, 1.18], [0.58, 0.62, 0.68, 1], rack_id,
                     {"roughness": 0.12, "metallic": 1.0})
            label_color = [0.04, 0.42, 0.9, 1] if row_name == "a" else [0.05, 0.72, 0.38, 1]
            box(f"{rack_id}_{face_name}_id_strip", [0.34, 0.024, 0.07],
                [x - 0.08, handle_y, 1.95], label_color, rack_id,
                {"roughness": 0.2, "metallic": 0.35, "bevel_width": 0.006},
                {"asset_type": "rack_identifier", "rack_id": rack_id, "label": rack_id.upper()})

scene["name"] = "Server room complexity level 4 - detailed racks"
output = folder / "server-room-l4.scene.json"
output.write_text(json.dumps(scene, indent=2) + "\n", encoding="utf-8")
print(f"Generated {len(objects)} semantic objects -> {output}")
