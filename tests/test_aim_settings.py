import unittest

from ext.datatypes import PLAYER_BONES
from functions.aim_settings import resolve_aim_bone_id


class AimSettingsTests(unittest.TestCase):
    def test_gui_labels_map_to_the_expected_bones(self):
        self.assertEqual(PLAYER_BONES["head"], resolve_aim_bone_id("Head"))
        self.assertEqual(PLAYER_BONES["neck_0"], resolve_aim_bone_id("Neck"))
        self.assertEqual(PLAYER_BONES["spine_2"], resolve_aim_bone_id("Torso"))
        self.assertEqual(PLAYER_BONES["leg_lower_L"], resolve_aim_bone_id("Leg"))

    def test_legacy_numeric_selection_is_supported(self):
        self.assertEqual(PLAYER_BONES["head"], resolve_aim_bone_id(0))
        self.assertEqual(PLAYER_BONES["neck_0"], resolve_aim_bone_id(1))
        self.assertEqual(PLAYER_BONES["spine_2"], resolve_aim_bone_id(2))
        self.assertEqual(PLAYER_BONES["leg_lower_L"], resolve_aim_bone_id(3))

    def test_invalid_selection_falls_back_to_head(self):
        self.assertEqual(PLAYER_BONES["head"], resolve_aim_bone_id("Unknown"))
        self.assertEqual(PLAYER_BONES["head"], resolve_aim_bone_id(99))


if __name__ == "__main__":
    unittest.main()
