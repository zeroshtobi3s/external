"""Shared validation for user-facing aim settings."""

from ext.datatypes import PLAYER_BONES

AIM_POSITION_NAMES = ("Head", "Neck", "Torso", "Leg")
AIM_POSITION_BONES = {
    "Head": "head",
    "Neck": "neck_0",
    "Torso": "spine_2",
    "Leg": "leg_lower_L",
}


def resolve_aim_bone_id(selected_position):
    """Return a valid bone ID for a GUI label or the legacy numeric selection."""
    if isinstance(selected_position, int) and 0 <= selected_position < len(AIM_POSITION_NAMES):
        selected_position = AIM_POSITION_NAMES[selected_position]
    bone_name = AIM_POSITION_BONES.get(selected_position, "head")
    return PLAYER_BONES[bone_name]
