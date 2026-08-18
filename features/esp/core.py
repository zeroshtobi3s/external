import globals
from ext.datatypes import *
from functions import calculations, memfuncs, player_resolver

try:
    import pymeow as pme
except ImportError:
    import pyMeow as pme
from features import spectator

from .colors import health_color_hex, resolve_color
from .draw import (
    draw_box,
    draw_distance,
    draw_health_bar,
    draw_health_text,
    draw_name,
    draw_skeleton,
)
from .entity_list import entity_list_chunk_address, entity_slot_address
from .fonts import _ensure_raylib_font, _find_overlay_font, _get_overlay_font_handle
from .visibility import is_visible_to_local, resolve_local_index

boneConnections = [
    ('head', 'neck_0'), ('neck_0', 'spine_1'), ('spine_1', 'spine_2'), ('spine_2', 'pelvis'),
    ('pelvis', 'leg_upper_L'), ('leg_upper_L', 'leg_lower_L'), ('leg_lower_L', 'ankle_L'),
    ('pelvis', 'leg_upper_R'), ('leg_upper_R', 'leg_lower_R'), ('leg_lower_R', 'ankle_R'),
    ('spine_2', 'arm_upper_L'), ('arm_upper_L', 'arm_lower_L'), ('arm_lower_L', 'hand_L'),
    ('spine_2', 'arm_upper_R'), ('arm_upper_R', 'arm_lower_R'), ('arm_lower_R', 'hand_R')
]


def _neron_has_focus():
    import win32gui
    try:
        hwnd = win32gui.FindWindow(None, "Counter-Strike 2")
        if hwnd:
            if win32gui.IsIconic(hwnd):
                return False
            return True
    except Exception:
        pass
    return True


def enforce_overlay_topmost():
    import win32con
    import win32gui
    try:
        hwnd = pme.get_window_handle()
        if hwnd and win32gui.IsWindow(hwnd):
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
            new_style = (style & ~win32con.WS_EX_APPWINDOW) | win32con.WS_EX_TOOLWINDOW | win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_LAYERED | win32con.WS_EX_NOACTIVATE
            if style != new_style:
                win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, new_style)
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW
            )
    except Exception:
        pass


def ESP_Update(processHandle, clientBaseAddress, Options, Offsets, SharedBombState, SharedRuntime=None):
    globals.update_screen_size()
    enforce_overlay_topmost()
    if not _neron_has_focus():
        try:
            pme.begin_drawing()
            pme.end_drawing()
        except Exception:
            pass
        return

    local_state = player_resolver.resolve_local_player(
        processHandle, clientBaseAddress, Offsets.offset
    )
    if local_state is None:
        return

    local_pawn = local_state.pawn
    local_controller = local_state.controller
    EntityList = local_state.entity_list
    try:
        local_team = memfuncs.ProcMemHandler.ReadInt(
            processHandle, local_pawn + Offsets.offset.m_iTeamNum
        )
        local_origin = memfuncs.ProcMemHandler.ReadVec(
            processHandle, local_pawn + Offsets.offset.m_vOldOrigin
        )
    except Exception:
        return

    # Gather toggles
    opt_box = Options.get("EnableESPBoxRendering", False)
    opt_name = Options.get("EnableESPNameText", False)
    opt_distance = Options.get("EnableESPDistanceText", False)
    opt_health_text = Options.get("EnableESPHealthText", False)
    opt_health_bar = Options.get("EnableESPHealthBarRendering", False)
    opt_tracer = Options.get("EnableESPTracerRendering", False)
    opt_skeleton = Options.get("EnableESPSkeletonRendering", False)
    opt_team_check = Options.get("EnableESPTeamCheck", False)
    opt_visible_box = Options.get("ESP_VisibleCheckBox", False)

    render_required = any((opt_box, opt_name, opt_distance, opt_health_text, opt_health_bar, opt_tracer, opt_skeleton))
    ct_color = Options.get("CT_color", "#4DA2FF"); t_color = Options.get("T_color", "#FF6A5A")
    ct_col = resolve_color(ct_color); t_col = resolve_color(t_color)

    # world scan
    scanned = []
    local_index = 0
    if EntityList and render_required:
        local_index = resolve_local_index(processHandle, EntityList, local_controller)
        for i in range(1, 65):
            try:
                chunk_address = entity_list_chunk_address(EntityList, i)
                list_entry = memfuncs.ProcMemHandler.ReadPointer(processHandle, chunk_address)
                if not list_entry:
                    continue
                controller = memfuncs.ProcMemHandler.ReadPointer(
                    processHandle, entity_slot_address(list_entry, i)
                )
                if not controller or controller == local_controller:
                    continue
                pawnHandle = memfuncs.ProcMemHandler.ReadInt(processHandle, controller + Offsets.offset.m_hPlayerPawn)
                if not pawnHandle:
                    continue
                pawn_chunk_address = entity_list_chunk_address(EntityList, pawnHandle)
                list_entry2 = memfuncs.ProcMemHandler.ReadPointer(processHandle, pawn_chunk_address)
                if not list_entry2:
                    continue
                pawn = memfuncs.ProcMemHandler.ReadPointer(
                    processHandle, entity_slot_address(list_entry2, pawnHandle)
                )
                if not pawn or pawn == local_pawn:
                    continue
                health = memfuncs.ProcMemHandler.ReadInt(processHandle, pawn + Offsets.offset.m_iHealth)
                team = memfuncs.ProcMemHandler.ReadInt(processHandle, pawn + Offsets.offset.m_iTeamNum)
                if not 0 < health <= 100 or (opt_team_check and team == local_team):
                    continue
                sceneNode = memfuncs.ProcMemHandler.ReadPointer(processHandle, pawn + Offsets.offset.m_pGameSceneNode)
                if not sceneNode:
                    continue
                boneMatrix = memfuncs.ProcMemHandler.ReadPointer(processHandle, sceneNode + Offsets.offset.m_modelState + 0x80)
                if not boneMatrix:
                    continue
                origin = memfuncs.ProcMemHandler.ReadVec(processHandle, pawn + Offsets.offset.m_vOldOrigin)
                head = memfuncs.ProcMemHandler.ReadVec(processHandle, boneMatrix + (6 * 32))
                if calculations.distance_vec3(origin, local_origin) < 35:
                    continue
                bones_world = None
                if opt_skeleton:
                    bones_world = {}
                    for bone_name, bone_index in PLAYER_BONES.items():
                        bones_world[bone_name] = memfuncs.ProcMemHandler.ReadVec(processHandle, boneMatrix + bone_index * 32)
                name = None
                if opt_name:
                    try:
                        addr = memfuncs.ProcMemHandler.ReadPointer(processHandle, controller + Offsets.offset.m_sSanitizedPlayerName)
                        name = memfuncs.ProcMemHandler.ReadString(processHandle, addr, 64) if addr else "?"
                    except Exception:
                        name = "?"
                visible = False
                if opt_visible_box:
                    visible = is_visible_to_local(processHandle, pawn, Offsets, local_index)
                scanned.append({'team':team,'health':health,'origin':origin,'head':head,'bones':bones_world,'name':name,'visible':visible})
            except Exception:
                continue

    # draw with fresh camera
    try:
        pme.begin_drawing()
    except Exception:
        return
    font_path = _find_overlay_font(); font_id = _ensure_raylib_font(); font_handle = _get_overlay_font_handle(16)
    try:
        specs_snapshot = []
        if SharedRuntime is not None:
            try:
                specs_snapshot = list(SharedRuntime.spectators)
            except Exception:
                specs_snapshot = []
        spectator.render_spectator_block(
            pme,
            specs_snapshot,
            enabled=Options.get("EnableShowSpectators", True),
            screen_size=(globals.SCREEN_WIDTH, globals.SCREEN_HEIGHT),
            font_path=font_path,
            font_id=font_id,
            font_handle=font_handle,
            font_size=16,
        )
    except Exception:
        pass
    try:
        viewMatrix = memfuncs.ProcMemHandler.ReadMatrix(processHandle, clientBaseAddress + Offsets.offset.dwViewMatrix)
    except Exception:
        viewMatrix = None
    if viewMatrix is None:
        try:
            pme.end_drawing()
        except Exception:
            pass
        return

    screen_w = globals.SCREEN_WIDTH; screen_h = globals.SCREEN_HEIGHT
    for ent in scanned:
        try:
            origin = ent['origin']; head = ent['head']
            sf = calculations.world_to_screen(viewMatrix, origin)
            bt = calculations.world_to_screen(viewMatrix, Vector3(origin.x, origin.y, origin.z + 72))
            if sf.x <= -1 or sf.y <= -1 or bt.x <= -1 or bt.y <= -1:
                continue
            box_h = sf.y - bt.y
            if box_h < 8.0 or box_h > 1800.0:
                continue
            rect_left = sf.x - box_h / 4; rect_top = bt.y; rect_w = box_h / 2; rect_h = box_h
            rect_cx = rect_left + rect_w / 2; rect_cy = rect_top + rect_h / 2; rect_right = rect_left + rect_w
            info_x = rect_right + 8; info_y = rect_top + 2

            team = ent['team']; health = ent['health']
            color_team = t_col if team == 2 else ct_col
            if opt_visible_box and not ent.get('visible', False):
                color_team = resolve_color("#FFFFFF")
            health_hex = health_color_hex(int(health))
            health_col = resolve_color(health_hex)

            sync_skel = bool(Options.get("ESP_HealthSyncSkeleton", True))
            sync_bar = bool(Options.get("ESP_HealthSyncBar", True))
            skel_scale = float(Options.get("ESP_SkeletonThicknessScale", 1.0) or 1.0)
            box_scale = float(Options.get("ESP_BoxThicknessScale", 1.0) or 1.0)
            bar_scale = float(Options.get("ESP_HealthBarThicknessScale", 1.0) or 1.0)

            if opt_box:
                draw_box(pme, rect_left, rect_top, rect_w, rect_h, color=color_team, thickness_scale=box_scale)
            info_cursor = info_y
            if opt_name and ent['name']:
                draw_name(pme, ent['name'].strip(), info_x, info_cursor, color="#E8F1FF")
                info_cursor += 14
            if opt_distance:
                dist2d = calculations.distance_vec3(origin, local_origin)
                draw_distance(pme, info_x, info_cursor, dist2d, color="#A4B0C3")
                info_cursor += 14
            if opt_health_text:
                draw_health_text(pme, info_x, info_cursor, health, color="#82FFAE")
            if opt_health_bar:
                draw_health_bar(pme, health, rect_left, rect_top, rect_h, thickness_scale=bar_scale, use_health_color=sync_bar, team_color=color_team, color_from_hex=health_hex)
            if opt_tracer:
                pme.draw_line(screen_w // 2, screen_h, rect_cx, rect_cy, color=color_team, thick=1.5)
            if opt_skeleton and ent['bones']:
                bones2d = {bn: calculations.world_to_screen(viewMatrix, wp) for bn, wp in ent['bones'].items()}
                sk_thick = max(0.9, min(1.8, rect_h * 0.012)) * skel_scale
                sk_radius = int(max(1.0, min(3.0, rect_h * 0.02)))
                skel_col = health_col if sync_skel else color_team
                draw_skeleton(pme, bones2d, boneConnections, color=skel_col, thickness=sk_thick, joint_radius=sk_radius)
        except Exception:
            continue

    # FOV circle & bomb card remain unchanged
    try:
        pme.draw_circle_lines(globals.SCREEN_WIDTH // 2, globals.SCREEN_HEIGHT // 2, Options["AimbotFOV"], pme.get_color(Options["FOV_color"]))
    except Exception:
        pass
    try:
        if Options.get("EnableESPBombTimer", False) and SharedBombState is not None:
            planted = getattr(SharedBombState, "bombPlanted", False)
            time_left = getattr(SharedBombState, "bombTimeLeft", -1)
            total_time = getattr(SharedBombState, "bombTimeTotal", 40)
            site = getattr(SharedBombState, "site", "")
            is_defusing = getattr(SharedBombState, "isDefusing", False)
            defuse_time_left = getattr(SharedBombState, "defuseTimeLeft", -1)
            from .draw import draw_bomb_status_card
            draw_bomb_status_card(pme, planted=planted, time_left=time_left, total_time=total_time or 40, site=site, is_defusing=is_defusing, defuse_time_left=defuse_time_left)
    except Exception:
        pass
    try:
        pme.end_drawing()
    except Exception:
        pass
