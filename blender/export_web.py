"""Export the managed Blender scene as GLB plus a web-facing asset manifest."""

import argparse
import json
import sys
from pathlib import Path

import bpy


def decode_metadata(obj):
    raw = obj.get("digital_twin_metadata", "{}")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return dict(raw) if raw else {}


def main():
    tail = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--glb", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args(tail)
    args.glb.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)

    collection = bpy.data.collections.get("DigitalTwinMVP")
    if collection is None:
        raise RuntimeError("DigitalTwinMVP collection not found")

    assets = []
    for obj in collection.all_objects:
        object_id = obj.get("digital_twin_id")
        if not object_id:
            continue
        metadata = decode_metadata(obj)
        assets.append({
            "object_id": object_id,
            "asset_id": metadata.get("asset_id"),
            "asset_type": metadata.get("asset_type", obj.get("primitive", "object")),
            "parent_id": obj.parent.get("digital_twin_id") if obj.parent else None,
            "metadata": metadata,
        })

    bpy.ops.export_scene.gltf(
        filepath=str(args.glb.resolve()), export_format="GLB", export_extras=True,
        export_materials="EXPORT", export_apply=True, export_animations=False,
        export_cameras=False, export_lights=False, use_active_scene=True,
    )
    manifest = {
        "scene_id": "server-room-l4",
        "scene_name": bpy.context.scene.get("digital_twin_scene", "Server room"),
        "generated_by": "ai-low-cost-digital-twin-mvp",
        "assets": assets,
    }
    args.manifest.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"MVP_WEB_EXPORT_OK glb={args.glb.resolve()} assets={len(assets)}")


if __name__ == "__main__":
    main()
