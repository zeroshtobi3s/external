import ctypes
import win32api, win32gui, win32con, win32process

from functions import logutil

user32 = ctypes.WinDLL('user32', use_last_error=True)
SetWindowDisplayAffinity = user32.SetWindowDisplayAffinity
SetWindowDisplayAffinity.argtypes = ctypes.wintypes.HWND, ctypes.wintypes.DWORD
SetWindowDisplayAffinity.restype = ctypes.wintypes.BOOL
WDA_EXCLUDEFROMCAPTURE = 0x00000011
WDA_NONE = 0x00000000

GUI_WINDOW_TITLE = "NERON CS2 External - Control Panel"
GAME_WINDOW_TITLE = "Counter-Strike 2"

HIDDEN = False
STREAMPROOF = False

def get_gui_hwnd():
	"""Find the NERON GUI window handle reliably."""
	hwnd = win32gui.FindWindow(None, GUI_WINDOW_TITLE)
	if hwnd and win32gui.IsWindow(hwnd):
		return hwnd
	
	# Fallback: enum windows to match title
	found = []
	def enum_handler(h, extra):
		if win32gui.IsWindow(h):
			text = win32gui.GetWindowText(h)
			if "NERON" in text and ("Control Panel" in text or "CS2" in text):
				found.append(h)
	try:
		win32gui.EnumWindows(enum_handler, None)
	except Exception:
		pass
	return found[0] if found else 0

def get_overlay_hwnd():
	"""Find the ESP overlay window handle."""
	for title in ["ESP-Overlay", "pyMeow", "Counter-Strike 2 Overlay"]:
		hwnd = win32gui.FindWindow(None, title)
		if hwnd and win32gui.IsWindow(hwnd):
			return hwnd
	return 0

def force_foreground(hwnd):
	"""Force window to foreground even when called from background thread or hotkey."""
	if not hwnd or not win32gui.IsWindow(hwnd):
		return
	try:
		cur_thread = win32api.GetCurrentThreadId()
		fg_hwnd = win32gui.GetForegroundWindow()
		fg_thread, _ = win32process.GetWindowThreadProcessId(fg_hwnd)
		if fg_thread != cur_thread and fg_thread != 0:
			win32process.AttachThreadInput(cur_thread, fg_thread, True)
			win32gui.SetForegroundWindow(hwnd)
			win32gui.BringWindowToTop(hwnd)
			win32gui.SetActiveWindow(hwnd)
			win32process.AttachThreadInput(cur_thread, fg_thread, False)
		else:
			win32gui.SetForegroundWindow(hwnd)
			win32gui.BringWindowToTop(hwnd)
			win32gui.SetActiveWindow(hwnd)
	except Exception:
		try:
			win32gui.SetForegroundWindow(hwnd)
			win32gui.BringWindowToTop(hwnd)
		except Exception:
			pass

def ensure_topmost(hwnd):
	"""Ensure window stays topmost over games."""
	if not hwnd or not win32gui.IsWindow(hwnd):
		return
	try:
		win32gui.SetWindowPos(
			hwnd,
			win32con.HWND_TOPMOST,
			0, 0, 0, 0,
			win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_SHOWWINDOW
		)
	except Exception:
		pass

def hide_dpg():
	"""Toggle GUI visibility, topmost status, and game focus."""
	global HIDDEN, STREAMPROOF
	hwnd = get_gui_hwnd()
	if not hwnd:
		logutil.debug("[gui_util] NERON GUI window not found")
		return

	is_visible = win32gui.IsWindowVisible(hwnd) and not HIDDEN

	if is_visible:
		# Hide GUI
		win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
		HIDDEN = True
		# Restore focus to game
		try:
			game_hwnd = win32gui.FindWindow(None, GAME_WINDOW_TITLE)
			if game_hwnd and win32gui.IsWindow(game_hwnd):
				force_foreground(game_hwnd)
		except Exception:
			pass
	else:
		# Show GUI on top of game
		win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
		win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
		ensure_topmost(hwnd)
		force_foreground(hwnd)
		if STREAMPROOF:
			SetWindowDisplayAffinity(hwnd, WDA_NONE)
			SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
		HIDDEN = False

def streamproof_toggle():
	global STREAMPROOF
	hwnd1 = get_gui_hwnd()
	hwnd2 = get_overlay_hwnd()
	if STREAMPROOF:
		logutil.info("STREAMPROOF OFF")
		if hwnd1:
			SetWindowDisplayAffinity(hwnd1, WDA_NONE)
		if hwnd2:
			SetWindowDisplayAffinity(hwnd2, WDA_NONE)
		STREAMPROOF = False
	else:
		logutil.info("STREAMPROOF ON")
		if hwnd1:
			SetWindowDisplayAffinity(hwnd1, WDA_EXCLUDEFROMCAPTURE)
		if hwnd2:
			SetWindowDisplayAffinity(hwnd2, WDA_EXCLUDEFROMCAPTURE)
		STREAMPROOF = True

