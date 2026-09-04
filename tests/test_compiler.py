import json
import unittest
from pathlib import Path

from digital_twin.compiler import SceneValidationError, compile_scene


class CompilerTests(unittest.TestCase):
    def test_example_compiles(self):
        scene = json.loads(Path("examples/desktop.scene.json").read_text(encoding="utf-8"))
        program = compile_scene(scene)
        self.assertEqual(program["ir_version"], "0.1")
        self.assertEqual(len(program["commands"]), 10)

    def test_duplicate_ids_are_rejected(self):
        scene = {"schema_version":"0.1", "objects":[
            {"id":"same","primitive":"sphere","radius":1},
            {"id":"same","primitive":"sphere","radius":1}]}
        with self.assertRaises(SceneValidationError):
            compile_scene(scene)

    def test_parent_and_metadata_are_preserved(self):
        scene = {"schema_version":"0.1", "objects":[
            {"id":"rack","primitive":"box","dimensions":[1,1,2]},
            {"id":"server","primitive":"box","dimensions":[0.8,0.1,0.2],
             "parent_id":"rack","metadata":{"asset_id":"SRV-001","status":"online"},
             "material":{"metallic":0.8,"roughness":0.25}}]}
        command = compile_scene(scene)["commands"][1]
        self.assertEqual(command["parent_id"], "rack")
        self.assertEqual(command["metadata"]["status"], "online")
        self.assertEqual(command["material"]["metallic"], 0.8)


if __name__ == "__main__":
    unittest.main()
