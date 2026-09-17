import unittest

from origami_visualizer import HexGussetMesh, OvphysxBridge, WaveScheduler
from origami_visualizer.usd_asset import write_stage


class CoreTests(unittest.TestCase):
    def test_hinges_are_unique_and_signed(self):
        mesh = HexGussetMesh(3, 3)
        self.assertEqual(mesh.summary(), {"panels": 9, "hinges": 16})
        self.assertEqual(len({hinge.id for hinge in mesh.hinges}), 16)
        self.assertEqual({hinge.fold_sign for hinge in mesh.hinges}, {-1, 1})

    def test_wave_reaches_distant_hex_later(self):
        scheduler = WaveScheduler(base_level=0, envelope_smoothing=1)
        scheduler.update_envelope(0)
        scheduler.add_onset_wave((0, 0), 0, speed=2, width=.25, lifetime=5)
        self.assertGreater(scheduler.fold_param((0, 0), 0), scheduler.fold_param((2, 0), 0))
        self.assertGreater(scheduler.fold_param((2, 0), 1), scheduler.fold_param((0, 0), 1))

    def test_drive_count_and_damping(self):
        mesh = HexGussetMesh(2, 2)
        commands = OvphysxBridge(mesh, damping=40).drive_commands(WaveScheduler(), 0)
        self.assertEqual(len(commands), len(mesh.hinges))
        self.assertTrue(all(command.damping == 40 for command in commands))

    def test_generated_usd_describes_panels_and_hinges(self):
        path = write_stage(".tmp-test.usda", 2, 2)
        content = path.read_text(encoding="utf-8")
        path.unlink()
        self.assertIn('def Xform "hex_0_0"', content)
        self.assertIn('origami:jointType = "revolute"', content)


if __name__ == "__main__":
    unittest.main()
