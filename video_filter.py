import ctypes
import json
import os
import sys
import time
import traceback

import cv2
import numpy as np
import pydirectinput
import win32api
import win32con
import win32gui
import win32process

from windows_capture import (
    WindowsCapture,
    Frame,
    InternalCaptureControl,
)


LIVE_WINDOW = "Simulator Live-Ansicht"

if getattr(sys, "frozen", False):
    RESSOURCEN_ORDNER = sys._MEIPASS
else:
    RESSOURCEN_ORDNER = os.path.dirname(os.path.abspath(__file__))

if getattr(sys, "frozen", False):
    DATEN_ORDNER = os.path.dirname(os.path.abspath(sys.executable))
else:
    DATEN_ORDNER = os.path.dirname(os.path.abspath(__file__))

ICON_PFAD = os.path.join(RESSOURCEN_ORDNER, "fpv_icon.ico")

KONFIG_DATEI = os.path.join(DATEN_ORDNER, "einstellungen.json")

AUFNAHME_ORDNER = os.path.join(DATEN_ORDNER, "Aufnahmen")

FPV_WIDTH = 800
FPV_HEIGHT = 480

SCANLINE_STRENGTH = 0.20
SCANLINE_PERIOD = 3
SCANLINE_SPEED = 0.3
NOISE_STRENGTH = 8

GLITCH_CHANCE = 0.03
GLITCH_MIN_DICKE = 4
GLITCH_MAX_DICKE = 14
GLITCH_MAX_VERSCHIEBUNG = 40

SIGNAL_LOSS_CHANCE = 0.001
SIGNAL_LOSS_MIN_FRAMES = 8
SIGNAL_LOSS_MAX_FRAMES = 20

BAD_SIGNAL_CHANCE = 0.0025
BAD_SIGNAL_MIN_FRAMES = 10
BAD_SIGNAL_MAX_FRAMES = 40
BAD_SIGNAL_STAERKE = 25

SPRACHE = "de"

CHROM_STAERKE = 3.0

scanline_offset = 0.0

signal_verlust_restframes = 0

bad_signal_restframes = 0

aufnahme_aktiv = False
video_writer = None 

TEXTE = {
    "de": {
        "rauschen": "Rauschen",
        "scanline_staerke": "Scanline Stärke",
        "scanline_speed": "Scanline Speed",
        "scanline_abstand": "Scanline Abstand",
        "glitch_chance": "Glitch Chance",
        "signalverlust_chance": "Signalverlust Chance",
        "bad_signal_chance": "Bad Signal Chance",
        "chromatik_staerke": "Chromatische Aberration",
        "sprache_label": "Sprache",
        "sprache_wert": "Deutsch",
        "no_signal_text": "KEIN SIGNAL",
        "preset_standard": "Standard",
        "preset_clean": "Clean",
        "preset_alter_fernseher": "Alter Fernseher",
        "preset_extrem_kaputt": "Extrem kaputt",
        "aufnahme_start": "Aufnahme gestartet",
        "aufnahme_stop": "Aufnahme gestoppt",
    },
    "en": {
        "rauschen": "Noise",
        "scanline_staerke": "Scanline Strength",
        "scanline_speed": "Scanline Speed",
        "scanline_abstand": "Scanline Spacing",
        "glitch_chance": "Glitch Chance",
        "signalverlust_chance": "Signal Loss Chance",
        "bad_signal_chance": "Bad Signal Chance",
        "chromatik_staerke": "Chromatic Aberration",
        "sprache_label": "Language",
        "sprache_wert": "English",
        "no_signal_text": "NO SIGNAL",
        "preset_standard": "Standard",
        "preset_clean": "Clean",
        "preset_alter_fernseher": "Old CRT",
        "preset_extrem_kaputt": "Extremely Trashed",
        "aufnahme_start": "Recording started",
        "aufnahme_stop": "Recording stopped",
    },
}


PRESETS = {
    "standard": {
        "rauschen": 8.0, "scanline_staerke": 0.2, "scanline_speed": 0.3,
        "scanline_abstand": 3.0, "glitch_chance": 0.03,
        "signalverlust_chance": 0.001, "bad_signal_chance": 0.0025,
        "chromatik_staerke": 1.0,
    },
    "clean": {
        "rauschen": 0.0, "scanline_staerke": 0.0, "scanline_speed": 0.0,
        "scanline_abstand": 3.0, "glitch_chance": 0.0,
        "signalverlust_chance": 0.0, "bad_signal_chance": 0.0,
        "chromatik_staerke": 0.0,
    },
    "alter_fernseher": {
        "rauschen": 8.0, "scanline_staerke": 0.35, "scanline_speed": 0.3,
        "scanline_abstand": 3.0, "glitch_chance": 0.01,
        "signalverlust_chance": 0.005, "bad_signal_chance": 0.01,
        "chromatik_staerke": 2.0,
    },
    "extrem_kaputt": {
        "rauschen": 25.0, "scanline_staerke": 0.7, "scanline_speed": 0.8,
        "scanline_abstand": 2.0, "glitch_chance": 0.08,
        "signalverlust_chance": 0.03, "bad_signal_chance": 0.06,
        "chromatik_staerke": 8.0,   
    },
}


def konfig_laden():
    try:
        with open(KONFIG_DATEI, "r", encoding="utf-8") as datei:
            return json.load(datei)
    except Exception:
        return {}


def konfig_speichern():
    daten = {
        "sprache": SPRACHE,
        "letztes_fenster": simulator_titel,
        "regler": {s["key"]: s["value"] for s in SLIDER_DEFS},
    }

    try:
        with open(KONFIG_DATEI, "w", encoding="utf-8") as datei:
            json.dump(daten, datei, indent=2, ensure_ascii=False)
    except Exception:
        print("Einstellungen konnten nicht gespeichert werden:")
        traceback.print_exc()

simulator_hwnd = 0
simulator_titel = ""

capture_control = None
programm_beenden = False
frame_empfangen = False
ist_vollbild = False

bild_breite = 0
bild_hoehe = 0


try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass


def simulator_icon_holen(hwnd):
    icon_gross = win32gui.SendMessage(
        hwnd, win32con.WM_GETICON, win32con.ICON_BIG, 0
    )

    ICON_SMALL2 = 2

    icon_klein = win32gui.SendMessage(
        hwnd, win32con.WM_GETICON, ICON_SMALL2, 0
    )
    if not icon_klein:
        icon_klein = win32gui.SendMessage(
            hwnd, win32con.WM_GETICON, win32con.ICON_SMALL, 0
        )

    if not icon_gross:
        icon_gross = win32gui.GetClassLong(hwnd, win32con.GCL_HICON)

    if not icon_klein:
        icon_klein = win32gui.GetClassLong(hwnd, win32con.GCL_HICONSM)

    if icon_gross and icon_klein:
        return icon_gross, icon_klein

    try:
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        prozess = win32api.OpenProcess(
            win32con.PROCESS_QUERY_INFORMATION
            | win32con.PROCESS_VM_READ,
            False,
            pid
        )

        exe_pfad = win32process.GetModuleFileNameEx(prozess, 0)

        win32api.CloseHandle(prozess)

        grosse_icons, kleine_icons = win32gui.ExtractIconEx(exe_pfad, 0)

        if grosse_icons and kleine_icons:
            return grosse_icons[0], kleine_icons[0]

    except Exception:
        print("Icon konnte nicht aus der .exe gelesenwerden:")
        traceback.print_exc()

    return None, None


def fenster_icon_direkt_setzen(fenster_titel, icon_gross, icon_klein):
    hwnd = win32gui.FindWindow(None, fenster_titel)

    if hwnd == 0:
        return

    if icon_gross:
        win32gui.SendMessage(
            hwnd, win32con.WM_SETICON, win32con.ICON_BIG, icon_gross
        )

    if icon_klein:
        win32gui.SendMessage(
            hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, icon_klein
        )
      

def fenster_icon_setzen(fenster_titel, icon_pfad):
    try:
        hwnd = win32gui.FindWindow(None, fenster_titel)

        if hwnd == 0:
            return

        icon_gross = win32gui.LoadImage(
            0,
            icon_pfad,
            win32con.IMAGE_ICON,
            32,
            32,
            win32con.LR_LOADFROMFILE
        )

        icon_klein = win32gui.LoadImage(
            0,
            icon_pfad,
            win32con.IMAGE_ICON,
            16,
            16,
            win32con.LR_LOADFROMFILE
        )

        win32gui.SendMessage(
            hwnd, win32con.WM_SETICON, win32con.ICON_BIG, icon_gross
        )

        win32gui.SendMessage(
            hwnd, win32con.WM_SETICON, win32con.ICON_SMALL, icon_klein
        )

    except Exception:
        print("Icon konnte nicht gesetzt werden:")
        traceback.print_exc()

def alle_fenster_auflisten():
    treffer = []

    def callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return
        
        titel = win32gui.GetWindowText(hwnd).strip()
        if not titel:
            return

        if win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) & win32con.WS_EX_TOOLWINDOW:
            return

        if titel in (LIVE_WINDOW, "Einstellungen"):
            return

        treffer.append((hwnd, titel))

    win32gui.EnumWindows(callback, None)

    return treffer


def simulator_groesse():
    if not win32gui.IsWindow(simulator_hwnd):
        return None

    links, oben, rechts, unten = (
        win32gui.GetClientRect(simulator_hwnd)
    )

    breite = rechts - links
    hoehe = unten - oben

    if breite <= 0 or hoehe <= 0:
        return None

    return breite, hoehe


def klick_an_simulator_senden(live_x, live_y):
    global bild_breite
    global bild_hoehe

    if bild_breite <= 0 or bild_hoehe <= 0:
        print("Noch kein Frame empfangen.")
        return

    simulator = simulator_groesse()

    if simulator is None:
        print("Simulatorfenster nicht mehr gefunden.")
        return

    simulator_breite, simulator_hoehe = simulator

    simulator_x = int(
        live_x * simulator_breite / bild_breite
    )

    simulator_y = int(
        live_y * simulator_hoehe / bild_hoehe
    )

    simulator_x = max(
        0,
        min(simulator_x, simulator_breite - 1)
    )

    simulator_y = max(
        0,
        min(simulator_y, simulator_hoehe - 1)
    )

    screen_x, screen_y = win32gui.ClientToScreen(
        simulator_hwnd,
        (simulator_x, simulator_y)
    )

    print(
        f"Klick Live=({live_x}, {live_y}) "
        f"Bild=({bild_breite}x{bild_hoehe}) "
        f"Simulator=({screen_x}, {screen_y})"
    )

    ursprung_x, ursprung_y = win32api.GetCursorPos()
    eigenes_fenster = win32gui.GetForegroundWindow()

    try:
        win32gui.SetForegroundWindow(simulator_hwnd)
    except Exception:
        pass

    pydirectinput.moveTo(
        screen_x,
        screen_y,
        duration=0
    )

    pydirectinput.mouseDown()
    pydirectinput.mouseUp()

    try:
        win32gui.SetForegroundWindow(eigenes_fenster)
    except Exception:
        pass

    pydirectinput.moveTo(
        ursprung_x,
        ursprung_y,
        duration=0
    )


def maus_callback(event, x, y, flags, userdata):
    if event == cv2.EVENT_LBUTTONDOWN:
        klick_an_simulator_senden(x, y)


def glitch_linien_einfuegen(small):
    if np.random.random() >= GLITCH_CHANCE:
        return small

    hoehe, breite = small.shape[:2]

    anzahl = np.random.randint(1, 3)

    for _ in range(anzahl):
        dicke = np.random.randint(
            GLITCH_MIN_DICKE,
            GLITCH_MAX_DICKE
        )

        start = np.random.randint(0, max(1, hoehe - dicke))

        versatz = np.random.randint(
            -GLITCH_MAX_VERSCHIEBUNG,
            GLITCH_MAX_VERSCHIEBUNG
        )

        streifen = small[start:start + dicke]

        streifen = np.roll(streifen, versatz, axis=1)

        helligkeit = np.random.uniform(0.6, 1.5)

        streifen = np.clip(
            streifen.astype(np.float32) * helligkeit,
            0,
            255
        ).astype("uint8")

        small[start:start + dicke] = streifen

    return small


def signal_verlust_bild(breite, hoehe):
    rauschen = np.random.randint(
        0,
        255,
        (hoehe, breite, 3),
        dtype=np.uint8
    )

    text = TEXTE[SPRACHE]["no_signal_text"]

    schrift = cv2.FONT_HERSHEY_SIMPLEX
    skala = breite / 400.0
    dicke = max(1, int(breite / 200))

    (text_breite, text_hoehe), _ = cv2.getTextSize(
        text,
        schrift,
        skala,
        dicke
    )

    x = (breite - text_breite) // 2
    y = (hoehe + text_hoehe) // 2

    cv2.putText(
        rauschen,
        text,
        (x, y),
        schrift,
        skala,
        (0, 0, 255),
        dicke,
        cv2.LINE_AA
    )

    return rauschen


def bad_signal_anwenden(small):
    hoehe, breite = small.shape[:2]

    versatz = np.random.randint(
        -BAD_SIGNAL_STAERKE,
        BAD_SIGNAL_STAERKE + 1,
        size=hoehe
    )

    spalten_index = (
        np.arange(breite)[None, :] - versatz[:, None]
    ) % breite

    zeilen_index = np.arange(hoehe)[:, None]

    return small[zeilen_index, spalten_index]


def chromatische_aberration_anwenden(small, staerke):
    versatz = int(round(staerke))

    if versatz <= 0:
        return small

    b, g, r = cv2.split(small)

    r = np.roll(r, versatz, axis=1)
    b = np.roll(b, - versatz, axis=1)

    return cv2.merge([b, g, r])


def fpv_filter_anwenden(bild):
    global scanline_offset
    global signal_verlust_restframes
    global bad_signal_restframes

    ziel_hoehe, ziel_breite = bild.shape[:2]

    small = cv2.resize(
        bild,
        (FPV_WIDTH, FPV_HEIGHT),
        interpolation=cv2.INTER_AREA
    )

    if signal_verlust_restframes > 0:
        signal_verlust_restframes -= 1

        small = signal_verlust_bild(FPV_WIDTH, FPV_HEIGHT)

        filtered = cv2.resize(
            small,
            (ziel_breite, ziel_hoehe),
            interpolation=cv2.INTER_NEAREST
        )

        return filtered

    if np.random.random() < SIGNAL_LOSS_CHANCE:
        signal_verlust_restframes = np.random.randint(
            SIGNAL_LOSS_MIN_FRAMES,
            SIGNAL_LOSS_MAX_FRAMES
        )

    hoehe = small.shape[0]
    zeilen = np.arange(hoehe)

    versatz = int(scanline_offset) % SCANLINE_PERIOD
    maske = ((zeilen + versatz) % SCANLINE_PERIOD) == 0

    linien = small[maske].astype(np.float32)

    variation = np.random.uniform(
        0.7,
        1.0,
        linien.shape[0]
    )

    variation = variation.reshape(-1, 1, 1)

    linien *= (
        1.0 - SCANLINE_STRENGTH * variation
    )

    small[maske] = np.clip(
        linien,
        0,
        255
    ).astype("uint8")

    scanline_offset += SCANLINE_SPEED

    if scanline_offset >= SCANLINE_PERIOD:
        scanline_offset -= SCANLINE_PERIOD

    small = glitch_linien_einfuegen(small)

    if bad_signal_restframes > 0:
        bad_signal_restframes -= 1
        small = bad_signal_anwenden(small)
    elif np.random.random() < BAD_SIGNAL_CHANCE:
        bad_signal_restframes = np.random.randint(
            BAD_SIGNAL_MIN_FRAMES,
            BAD_SIGNAL_MAX_FRAMES
        )
        small = bad_signal_anwenden(small)

    noise = np.random.normal(
        0,
        NOISE_STRENGTH,
        small.shape
    )

    noisy = small.astype(np.float32) + noise

    small = np.clip(
        noisy,
        0,
        255
    ).astype("uint8")

    small = chromatische_aberration_anwenden(small, CHROM_STAERKE)

    filtered = cv2.resize(
        small,
        (ziel_breite, ziel_hoehe),
        interpolation=cv2.INTER_NEAREST
    )

    return filtered


def trackbar_dummy(wert):

    pass

PANEL_BREITE = 420
PANEL_RAND = 20
PANEL_ZEILE = 70
PANEL_SLIDER_HOEHE = 18

SLIDER_DEFS = [
    {"key": "rauschen",
     "min": 0.0, "max": 40.0, "value": float(NOISE_STRENGTH)},
    {"key": "scanline_staerke",
     "min": 0.0, "max": 1.0, "value": SCANLINE_STRENGTH},
    {"key": "scanline_speed",
     "min": 0.0, "max": 2.0, "value": SCANLINE_SPEED},
    {"key": "scanline_abstand",
     "min": 1.0, "max": 20.0, "value": float(SCANLINE_PERIOD)},
    {"key": "glitch_chance",
     "min": 0.0, "max": 0.1, "value": GLITCH_CHANCE},
    {"key": "signalverlust_chance",
     "min": 0.0, "max": 0.01, "value": SIGNAL_LOSS_CHANCE},
    {"key": "bad_signal_chance",
     "min": 0.0, "max": 0.02, "value": BAD_SIGNAL_CHANCE},
    {"key": "chromatik_staerke",
     "min": 0.0, "max": 15.0, "value": CHROM_STAERKE},
]

_gespeicherte_konfig = konfig_laden()

if _gespeicherte_konfig.get("sprache") in TEXTE:
    SPRACHE = _gespeicherte_konfig["sprache"]

if "regler" in _gespeicherte_konfig:
    for _s in SLIDER_DEFS:
        if _s["key"] in _gespeicherte_konfig["regler"]:
            _s["value"] = _gespeicherte_konfig["regler"][_s["key"]]

slider_wird_gezogen = None

sprache_button_rect = None

preset_button_rects = {}


def slider_index_bei_position(x, y):
    for i, s in enumerate(SLIDER_DEFS):
        if "rect" not in s:
            continue

        x1, y1, x2, y2 = s["rect"]

        if x1 <= x <= x2 and y1 - 8 <= y <= y2 + 8:
            return i

    return None

def slider_wert_aus_maus_setzen(i, x):
    s = SLIDER_DEFS[i]

    x1, _, x2, _ = s["rect"]

    anteil = (x - x1) / (x2 - x1)
    anteil = max(0.0, min(1.0, anteil))

    s["value"] = s["min"] + anteil * (s["max"] - s["min"])


def preset_anwenden(name):
    werte = PRESETS.get(name)

    if not werte:
        return

    for s in SLIDER_DEFS:
        if s["key"] in werte:
            s["value"] = werte[s["key"]]

def einstellungen_maus_callback(event, x, y, flags, userdata):
    global slider_wird_gezogen
    global SPRACHE

    if event == cv2.EVENT_LBUTTONDOWN:
        if sprache_button_rect is not None:
            bx1, by1, bx2, by2 = sprache_button_rect

            if bx1 <= x <= bx2 and by1 <= y <= by2:
                SPRACHE = "en" if SPRACHE == "de" else "de"
                return

        for preset_name, rect in preset_button_rects.items():
            px1, py1, px2, py2 = rect

            if px1 <= x <= px2 and py1 <= y <= py2:
                preset_anwenden(preset_name)
                return
            
        i = slider_index_bei_position(x, y)

        if i is not None:
            slider_wird_gezogen = i
            slider_wert_aus_maus_setzen(i, x)

    elif event == cv2.EVENT_MOUSEMOVE:
        if (
            slider_wird_gezogen is not None
            and flags & cv2.EVENT_FLAG_LBUTTON
        ):
            slider_wert_aus_maus_setzen(slider_wird_gezogen, x)

    elif event == cv2.EVENT_LBUTTONUP:
        slider_wird_gezogen = None

def einstellungen_panel_zeichnen():
    global sprache_button_rect
    global preset_button_rects

    SPRACHE_ZEILE = 55
    PRESET_ZEILE = 55

    hoehe = (
        PANEL_RAND * 2
        + SPRACHE_ZEILE
        + PRESET_ZEILE
        + len(SLIDER_DEFS) * PANEL_ZEILE
    )

    panel = np.full(
        (hoehe, PANEL_BREITE, 3),
        30,
        dtype=np.uint8
    )

    sprache_text = (
        f"{TEXTE[SPRACHE]['sprache_label']}: "
        f"{TEXTE[SPRACHE]['sprache_wert']}"
    )

    (text_breite, text_hoehe), _ = cv2.getTextSize(
        sprache_text,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        2
    )

    btn_x1 = PANEL_RAND
    btn_y1 = PANEL_RAND
    btn_x2 = btn_x1 + text_breite + 20
    btn_y2 = btn_y1 + text_hoehe + 20

    cv2.rectangle(
        panel,
        (btn_x1, btn_y1),
        (btn_x2, btn_y2),
        (0, 130, 190),
        -1
    )

    cv2.rectangle(
        panel,
        (btn_x1, btn_y1),
        (btn_x2, btn_y2),
        (255, 255, 255),
        1
    )

    cv2.putText(
        panel,
        sprache_text,
        (btn_x1 + 10, btn_y1 + text_hoehe + 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    sprache_button_rect = (btn_x1, btn_y1, btn_x2, btn_y2)

    preset_button_rects = {}

    preset_namen = ["standard", "clean", "alter_fernseher", "extrem_kaputt"]
    preset_y1 = btn_y2 + 15
    preset_y2 = preset_y1 + 32
    preset_x = PANEL_RAND
    preset_abstand = 10

    for preset_name in preset_namen:
        label = TEXTE[SPRACHE][f"preset_{preset_name}"]

        (label_breite, label_hoehe), _ = cv2.getTextSize(
            label,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            1
        )

        preset_x2 = preset_x + label_breite + 20

        cv2.rectangle(
            panel,
            (preset_x, preset_y1),
            (preset_x2, preset_y2),
            (70, 70, 70),
            -1
        )

        cv2.rectangle(
            panel,
            (preset_x, preset_y1),
            (preset_x2, preset_y2),
            (200, 200, 200),
            1
        )

        cv2.putText(
            panel,
            label,
            (preset_x + 10, preset_y2 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        preset_button_rects[preset_name] = (
            preset_x, preset_y1, preset_x2, preset_y2
        )

        preset_x = preset_x2 + preset_abstand

    for i, s in enumerate(SLIDER_DEFS):
        y_basis = (
            PANEL_RAND + SPRACHE_ZEILE + PRESET_ZEILE + i * PANEL_ZEILE
        )

        label = TEXTE[SPRACHE][s["key"]]
        text = f"{label}: {s['value']:.3f}"

        cv2.putText(
            panel,
            text,
            (PANEL_RAND, y_basis + 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )

        bar_x1 = PANEL_RAND
        bar_x2 = PANEL_BREITE - PANEL_RAND
        bar_y1 = y_basis + 28
        bar_y2 = bar_y1 + PANEL_SLIDER_HOEHE

        cv2.rectangle(
            panel,
            (bar_x1, bar_y1),
            (bar_x2, bar_y2),
            (80, 80, 80),
            -1
        )

        anteil = (s["value"] - s["min"]) / (s["max"] - s["min"])
        fuell_x2 = int(bar_x1 + anteil * (bar_x2 - bar_x1))

        cv2.rectangle(
            panel,
            (bar_x1, bar_y1),
            (fuell_x2, bar_y2),
            (0, 180, 255),
            -1
        )

        cv2.rectangle(
            panel,
            (bar_x1, bar_y1),
            (bar_x2, bar_y2),
            (200, 200, 200),
            1
        )

        s["rect"] = (bar_x1, bar_y1, bar_x2, bar_y2)

    return panel

def einstellungsfenster_erstellen():
    cv2.namedWindow("Einstellungen", cv2.WINDOW_NORMAL)

    cv2.setMouseCallback(
        "Einstellungen",
        einstellungen_maus_callback
    )

def einstellungen_auslesen():
    global NOISE_STRENGTH
    global SCANLINE_STRENGTH
    global SCANLINE_SPEED
    global SCANLINE_PERIOD
    global GLITCH_CHANCE
    global SIGNAL_LOSS_CHANCE
    global BAD_SIGNAL_CHANCE
    global CHROM_STAERKE

    werte = {s["key"]: s["value"] for s in SLIDER_DEFS}

    NOISE_STRENGTH = werte["rauschen"]
    SCANLINE_STRENGTH = werte["scanline_staerke"]
    SCANLINE_SPEED = werte["scanline_speed"]
    SCANLINE_PERIOD = max(1, int(round(werte["scanline_abstand"])))
    GLITCH_CHANCE = werte["glitch_chance"]
    SIGNAL_LOSS_CHANCE = werte["signalverlust_chance"]
    BAD_SIGNAL_CHANCE = werte["bad_signal_chance"]
    CHROM_STAERKE = werte["chromatik_staerke"]

    panel = einstellungen_panel_zeichnen()

    cv2.imshow("Einstellungen", panel)


def vollbild_umschalten():
    global ist_vollbild

    ist_vollbild = not ist_vollbild

    if ist_vollbild:
        cv2.setWindowProperty(
            LIVE_WINDOW,
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_FULLSCREEN
        )
        print("Vollbild AN (borderless)")
    else:
        cv2.setWindowProperty(
            LIVE_WINDOW,
            cv2.WND_PROP_FULLSCREEN,
            cv2.WINDOW_NORMAL
        )
        cv2.resizeWindow(
            LIVE_WINDOW,
            1000,
            700
        )
        print("Vollbild AUS")


def aufnahme_start_stop(breite, hoehe):
    global aufnahme_aktiv
    global video_writer

    if aufnahme_aktiv:
        aufnahme_aktiv = False

        if video_writer is not None:
            video_writer.release()
            video_writer = None

        print(TEXTE[SPRACHE]["aufnahme_stop"])
        return

    try:
        os.makedirs(AUFNAHME_ORDNER, exist_ok=True)

        dateiname = os.path.join(
            AUFNAHME_ORDNER,
            f"aufnahme_{time.strftime('%Y%m%d_%H%M%S')}.mp4"
        )

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        video_writer = cv2.VideoWriter(
            dateiname, fourcc, 30.0, (breite, hoehe)
        )

        aufnahme_aktiv = True

        print(f"{TEXTE[SPRACHE]['aufnahme_start']}: {dateiname}")

    except Exception:
        print(f"Aufnahme konnte nicht gestartet werden:")
        traceback.print_exc()
        aufnahme_aktiv = False
        video_writer = None


def screenshot_erstellen(bild):
    try:
        os.makedirs(AUFNAHME_ORDNER, exist_ok=True)

        dateiname = os.path.join(
            AUFNAHME_ORDNER,
            f"screenshot_{time.strftime('%Y%m%d_%H%M%S')}.png"
        )

        cv2.imwrite(dateiname, bild)

        print(f"Screenshot gespeichert: {dateiname}")

    except Exception:
        print("Screenshot konnte nicht gespeichert werden:")
        traceback.print_exc()


def beenden():
    global programm_beenden
    global capture_control
    global aufnahme_aktiv
    global video_writer

    programm_beenden = True

    if aufnahme_aktiv and video_writer is not None:
        video_writer.release()
        video_writer = None
        aufnahme_aktiv = False

    konfig_speichern()

    if capture_control is not None:
        try:
            capture_control.stop()
        except Exception:
            pass


# --------------------------------------------------
# Simulatorfenster auswählen
# --------------------------------------------------

treffer = alle_fenster_auflisten()

if not treffer:
    print("Keine offenen Fenster gefunden.")
    input("Enter zum Beenden...")
    sys.exit(1)

letztes_fenster_name = _gespeicherte_konfig.get("letztes_fenster")
auto_auswahl_index = None

if letztes_fenster_name:
    for _idx, (_, _titel) in enumerate(treffer):
        if _titel == letztes_fenster_name:
            auto_auswahl_index = _idx
            break

if auto_auswahl_index is not None:
    auswahl = auto_auswahl_index + 1
    print(f"Letztes Fenster automatisch gefunden: {letztes_fenster_name}")
else:
    print("\nOffene Fenster:")

    for nummer, (_, titel) in enumerate(treffer, start=1):
        print(f"{nummer}: {titel}")

    try:
        auswahl = int(input("\nNummer auswählen: "))
    except ValueError:
        print("Bitte eine Zahl eingeben.")
        input("Enter zum Beenden...")
        sys.exit(1)

    if auswahl < 1 or auswahl > len(treffer):
        print("Ungültige Auswahl.")
        input("Enter zum Beenden...")
        sys.exit(1)

simulator_hwnd, simulator_titel = treffer[auswahl - 1]

LIVE_WINDOW = f"{simulator_titel} Video Filter"

print(f"\nAusgewählt: {simulator_titel}")
print("Linksklick im Livebild wird an den Simulator weitergegeben.")
print("F schaltet Borderless-Vollbild um.")
print("R startet/stoppt eine Videoaufnahme.")
print("S speichert einen Screenshot.")
print("Q beendet das Programm.")


# --------------------------------------------------
# Windows-Capture VORBEREITEN
# --------------------------------------------------

capture = WindowsCapture(
    cursor_capture=False,
    draw_border=False,
    monitor_index=None,

    window_hwnd=simulator_hwnd
)


# --------------------------------------------------
# Livefenster öffnen
# --------------------------------------------------

cv2.namedWindow(
    LIVE_WINDOW,
    cv2.WINDOW_NORMAL
)

cv2.resizeWindow(
    LIVE_WINDOW,
    1000,
    700
)

cv2.setMouseCallback(
    LIVE_WINDOW,
    maus_callback
)

try:
    simulator_icon_gross, simulator_icon_klein = simulator_icon_holen(
        simulator_hwnd
    )
except Exception:
    print("Simulator-Icon konnte nicht geholt werden:")
    traceback.print_exc()
    simulator_icon_gross, simulator_icon_klein = None, None

if simulator_icon_gross and simulator_icon_klein:
    fenster_icon_direkt_setzen(
        LIVE_WINDOW, simulator_icon_gross, simulator_icon_klein
    )
else:
    print("Konnte Simulator-Icon nicht auslesen, nutze Standard-Icon.")
    fenster_icon_setzen(LIVE_WINDOW, ICON_PFAD)

einstellungsfenster_erstellen()

if simulator_icon_gross and simulator_icon_klein:
    fenster_icon_direkt_setzen(
        "Einstellungen", simulator_icon_gross, simulator_icon_klein
    )
else:
    fenster_icon_setzen("Einstellungen", ICON_PFAD)

time.sleep(0.5)


# --------------------------------------------------
# Windows-Capture Events registrieren
# --------------------------------------------------

@capture.event
def on_frame_arrived(
    frame: Frame,
    control: InternalCaptureControl
):
    global capture_control
    global bild_breite
    global bild_hoehe
    global frame_empfangen

    capture_control = control
    frame_empfangen = True

    if programm_beenden:
        control.stop()
        return

    try:
        bild = frame.frame_buffer

        if bild is None:
            return

        bild = np.asarray(bild)

        if bild.ndim != 3:
            print("Ungültiges Bildformat:", bild.shape)
            control.stop()
            return

        if bild.shape[2] == 4:
            bild = cv2.cvtColor(
                bild,
                cv2.COLOR_BGRA2BGR
            )

        bild_hoehe, bild_breite = bild.shape[:2]

        einstellungen_auslesen()

        bild = fpv_filter_anwenden(bild)

        cv2.imshow(
            LIVE_WINDOW,
            bild
        )

        taste = cv2.waitKey(1) & 0xFF

        if taste == ord("q"):
            beenden()

        if taste == ord("f"):
            vollbild_umschalten()

        if taste == ord("r"):
            aufnahme_start_stop(bild.shape[1], bild.shape[0])
        
        if taste == ord("s"):
            screenshot_erstellen(bild)
     
        if aufnahme_aktiv and video_writer is not None:
            video_writer.write(bild)

        if cv2.getWindowProperty(
            LIVE_WINDOW,
            cv2.WND_PROP_VISIBLE
        ) < 1:
            beenden()

    except Exception:
        print("\nFehler im Frame-Callback:")
        traceback.print_exc()
        control.stop()


@capture.event
def on_closed():
    global programm_beenden
    programm_beenden = True
    cv2.destroyAllWindows()


try:
    capture.start()

except Exception:
    print("\nFehler beim Starten der Aufnahme:")
    traceback.print_exc()

finally:
    programm_beenden = True

    if aufnahme_aktiv and video_writer is not None:
        try:
            video_writer.release()
        except Exception:
            pass

    try:
        konfig_speichern()
    except Exception:
        pass

    cv2.destroyAllWindows()
    print("Programm beendet.")
    input("Enter zum Schließen...")