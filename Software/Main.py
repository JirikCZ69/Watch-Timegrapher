import sys
import os
import json
import numpy as np
import sounddevice as sd
import scipy.signal as signal
from PyQt5 import QtWidgets, QtCore, QtGui, QtPrintSupport
import pyqtgraph as pg
from datetime import datetime
from collections import deque

class ThemeEngine:
    THEMES = {
        "AURIVON_NEON": {
            "bg_main": "#030303", "bg_panel": "#0A0A0A", "bg_sidebar": "#080808",
            "border": "#2A2A2A", "border_focus": "#00E5FF",
            "text_main": "#EEEEEE", "text_muted": "#666666",
            "accent_1": "#00E5FF", "accent_2": "#FF3366", "accent_ok": "#00FF66",
            "btn_bg": "#050505", "font_family": "Segoe UI"
        },
        "DARK_LUXURY": {
            "bg_main": "#0D0E11", "bg_panel": "#14151A", "bg_sidebar": "#101115",
            "border": "#26231C", "border_focus": "#D4AF37", # Zlato
            "text_main": "#E8E6E3", "text_muted": "#7A7873",
            "accent_1": "#D4AF37", "accent_2": "#E85D4E", "accent_ok": "#4E9C81",
            "btn_bg": "#1A1B22", "font_family": "Optima, Segoe UI"
        },
        "LIGHT_LUXURY": {
            "bg_main": "#F8F9FA", "bg_panel": "#FFFFFF", "bg_sidebar": "#F1F3F5",
            "border": "#E9ECEF", "border_focus": "#B76E79", # Rose Gold
            "text_main": "#212529", "text_muted": "#868E96",
            "accent_1": "#B76E79", "accent_2": "#D6336C", "accent_ok": "#20C997",
            "btn_bg": "#FFFFFF", "font_family": "Didot, Segoe UI"
        }
    }

    @classmethod
    def generate_stylesheet(cls, theme_name: str) -> str:
        t = cls.THEMES[theme_name]
        return f"""
        QMainWindow {{ background-color: {t['bg_main']}; }}
        QWidget {{ font-family: "{t['font_family']}", Arial; color: {t['text_main']}; }}
        
        QListWidget#Sidebar {{ background-color: {t['bg_sidebar']}; border-right: 1px solid {t['border']}; padding-top: 20px; outline: none; }}
        QListWidget#Sidebar::item {{ height: 65px; padding-left: 20px; border-left: 4px solid transparent; font-size: 14px; font-weight: bold; letter-spacing: 2px; color: {t['text_muted']}; }}
        QListWidget#Sidebar::item:selected {{ color: {t['accent_1']}; background-color: {t['bg_panel']}; border-left: 4px solid {t['accent_1']}; }}
        QListWidget#Sidebar::item:hover:!selected {{ color: {t['text_main']}; }}

        QGroupBox {{ border: 1px solid {t['border']}; border-radius: 4px; margin-top: 20px; padding-top: 30px; font-size: 13px; font-weight: bold; letter-spacing: 2px; color: {t['accent_1']}; background-color: {t['bg_panel']}; }}
        QGroupBox::title {{ subcontrol-origin: margin; subcontrol-position: top left; left: 20px; padding: 0 5px; color: {t['accent_1']}; }}

        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {{ background-color: {t['bg_main']}; border: 1px solid {t['border']}; border-radius: 2px; padding: 10px; color: {t['text_main']}; font-weight: bold; font-size: 14px; }}
        QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover {{ border: 1px solid {t['border_focus']}; }}
        
        QPushButton {{ border-radius: 2px; font-weight: bold; letter-spacing: 1.5px; background-color: {t['btn_bg']}; }}
        
        QTextEdit {{ background-color: {t['bg_main']}; border: 1px solid {t['border']}; padding: 15px; color: {t['text_main']}; }}
        QTextEdit#AnalysisPanel {{ background-color: {t['bg_sidebar']}; font-family: "Consolas"; color: {t['accent_ok']}; border: 1px solid {t['border']}; }}
        
        QWidget#BorderBox {{ border: 1px solid {t['border']}; background-color: {t['bg_panel']}; border-radius: 4px; }}
        """

STYLESHEET = """
QMainWindow { background-color: #030303; }
QWidget { font-family: "Segoe UI", Arial, sans-serif; color: #EEEEEE; }

QListWidget#Sidebar { background-color: #080808; border-right: 1px solid #1A1A1A; padding-top: 20px; outline: none; }
QListWidget#Sidebar::item { height: 60px; padding-left: 20px; border-left: 4px solid transparent; font-size: 13px; font-weight: bold; letter-spacing: 1px; color: #666666; }
QListWidget#Sidebar::item:selected { color: #00E5FF; background-color: #0D0D0D; border-left: 4px solid #00E5FF; }
QListWidget#Sidebar::item:hover:!selected { background-color: #0D0D0D; color: #FFFFFF; }

QGroupBox { border: 1px solid #2A2A2A; border-radius: 0px; margin-top: 15px; padding-top: 25px; font-size: 13px; font-weight: bold; letter-spacing: 2px; color: #00E5FF; background-color: #0A0A0A; }
QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; left: 15px; padding: 0 5px; color: #00E5FF; }

QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit { background-color: #121212; border: 1px solid #333333; border-radius: 0px; padding: 8px; color: #00E5FF; font-weight: bold; font-size: 14px; }
QComboBox::drop-down { border: none; }
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover, QLineEdit:hover { border: 1px solid #00E5FF; }
QComboBox QAbstractItemView { background-color: #0A0A0A; color: #FFFFFF; border: 1px solid #333333; selection-background-color: #00E5FF; selection-color: #000000; outline: none; }

QCheckBox { font-size: 14px; font-weight: bold; color: #00E5FF; spacing: 10px; }
QCheckBox::indicator { width: 18px; height: 18px; background-color: #121212; border: 1px solid #333333; }
QCheckBox::indicator:checked { background-color: #00E5FF; }

QSlider::groove:horizontal { border: 1px solid #333333; height: 4px; background: #000000; }
QSlider::handle:horizontal { background: #00E5FF; width: 10px; margin: -8px 0; }

QPushButton { border-radius: 0px; font-weight: bold; letter-spacing: 1px; }
QLabel { color: #FFFFFF; font-size: 14px; }

QTextEdit { background-color: #121212; border: 1px solid #333333; padding: 15px; font-family: "Segoe UI", Arial; font-size: 14px; color: #FFFFFF; }
QTextEdit:hover { border: 1px solid #00E5FF; }
QTextEdit#AnalysisPanel, QTextEdit#ProtocolData { background-color: #080808; border: 1px solid #2A2A2A; padding: 20px; font-family: "Consolas", monospace; font-size: 14px; color: #00FF66; }

QListWidget#HistoryList { background-color: #0A0A0A; border: 1px solid #222; padding: 10px; outline: none; }
QListWidget#HistoryList::item { color: #00E5FF; font-size: 14px; padding: 15px; border-bottom: 1px solid #1A1A1A; }
QListWidget#HistoryList::item:selected { background-color: #111; color: #FFFFFF; border-left: 3px solid #00E5FF; }

QMessageBox, QInputDialog { background-color: #0D0D0D; border: 1px solid #333333; }
QMessageBox QLabel, QInputDialog QLabel { color: #FFFFFF; font-size: 14px; font-weight: normal; }
QMessageBox QPushButton, QInputDialog QPushButton { background-color: #050505; border: 1px solid #00E5FF; color: #00E5FF; padding: 8px 20px; min-width: 80px; }
QMessageBox QPushButton:hover, QInputDialog QPushButton:hover { background-color: #00E5FF; color: #000000; }

QWidget#BorderBox { border: 1px solid #333333; background-color: #0A0A0A; }
"""

DATA_FILE = "timegrapher_data.json"


# ═══════════════════════════════════════════════════════════════════════════
#  AMPLITUDE KALKULÁTOR  – Block-Energy Group Method
#
#  Metoda kalibrovaná na reálných nahrávkách z piezo 27mm + Vorkoetter 6000×:
#
#  Vzorec:  A = (3600 × LA) / (T_tick × π × BPH)
#
#  T_tick = šířka energetické skupiny(n) tiku [s], měřená v 1ms blocích
#           s adaptivním prahem závisejícím na BPH.
#
#  PROČ NE KLASICKÁ T13 PEAK METODA:
#    Piezo 27mm + 6000× gain vytváří komplexní signál s mnoha dozvukovými
#    peaky. Klasická detekce 3 peaků (unlock/impulz/lock) nefunguje –
#    lock klik se topí v dozvuku a první dva kliknutí jsou těsně za sebou (~2ms).
#
#  BLOCK-ENERGY GROUP METODA:
#    1. Filtr 1000-8000 Hz (amplitude filter, ostré hrany)
#    2. Rozdělení 35ms okna na 1ms bloky
#    3. Adaptivní práh: thr = 0.22 + (BPH - 18000) × 4.63e-6
#       (kalibrováno na 18000 BPH → 233° a 28800 BPH → 230°)
#    4. Aktivní bloky = bloky nad prahem
#    5. Skupiny = clustery aktivních bloků s mezerou ≤ 2ms
#    6. T_tick = od začátku skupiny 1 do konce skupiny 2 (nebo jen 1 skupiny)
#    7. KLÍČ: odd/even separace – průměr mediánů eliminuje beat error bias
#
#  PŘESNOST (ověřeno na nahrávkách):
#    28800 BPH / LA=52°: 229.9° vs 230.0° cíl → chyba 0.1°
#    18000 BPH / LA=52°: 236.5° vs 233.0° cíl → chyba 3.5°
# ═══════════════════════════════════════════════════════════════════════════

class AmplitudeEstimator:
    """
    Výpočet amplitudy – Block-Energy Group metoda.
    Kalibrována na reálném signálu piezo 27mm + Vorkoetter TL074 6000×.
    """

    # Amplitudy mimo tento rozsah jsou fyzikálně nemožné → zahodit
    AMP_MIN = 120.0
    AMP_MAX = 360.0

    def __init__(self, sample_rate: int):
        self.sample_rate = sample_rate
        # Oddělené T13 zásobníky pro sudé/liché tiký (eliminuje beat error bias)
        self._t13_even: deque = deque(maxlen=80)
        self._t13_odd:  deque = deque(maxlen=80)
        self._amp_output: deque = deque(maxlen=30)
        # Sekundární filtr pro amplitude measurement (1000-8000 Hz)
        self._sos_amp = None
        self._zi_amp  = None

    def reset(self):
        self._t13_even.clear()
        self._t13_odd.clear()
        self._amp_output.clear()

    def setup_amp_filter(self, sample_rate: int):
        """Inicializuje sekundární filtr pro měření amplitudy."""
        self.sample_rate = sample_rate
        self._sos_amp = signal.butter(
            4, [1000, min(8000, sample_rate // 2 - 100)],
            btype='bandpass', fs=sample_rate, output='sos'
        )
        self._zi_amp = signal.sosfilt_zi(self._sos_amp)

    @staticmethod
    def adaptive_threshold(bph: int) -> float:
        """
        BPH-adaptivní práh pro skupinovou detekci.

        Kalibrační data:
          18000 BPH → thr = 0.220  (T13=14.0ms → 233°)
          28800 BPH → thr = 0.270  (T13= 9.0ms → 230°)
        Lineární extrapolace s clampem [0.14, 0.38].
        """
        return float(np.clip(0.22 + (bph - 18000) * 4.63e-6, 0.14, 0.38))

    def compute_t13_from_window(self, audio_window: np.ndarray, bph: int) -> float | None:
        """
        Vypočítá T_tick z audio okna 35ms pomocí Block-Energy Group metody.

        Parametry:
          audio_window – signál FILTROVANÝ pásmovým filtrem 1000-8000 Hz
          bph          – aktuální BPH hodinek

        Vrátí T_tick v sekundách nebo None.
        """
        if len(audio_window) < 10:
            return None

        beat_interval = 3600.0 / bph
        thr = self.adaptive_threshold(bph)

        # 1ms bloky – max amplituda každého bloku normalizovaná na max okna
        step = max(1, int(self.sample_rate * 0.001))
        n_blocks = len(audio_window) // step
        if n_blocks < 4:
            return None

        env_abs = np.abs(audio_window)
        max_v = np.max(env_abs)
        if max_v < 1e-6:
            return None

        block_amp = np.array([
            np.max(env_abs[b * step:(b + 1) * step]) / max_v
            for b in range(n_blocks)
        ])

        # Aktivní bloky nad adaptivním prahem
        active = np.where(block_amp >= thr)[0].tolist()
        if len(active) < 2:
            return None

        # Seskup aktivní bloky (max mezera 2ms = 2 bloky)
        groups: list[list[int]] = []
        grp = [active[0]]
        for i in range(1, len(active)):
            if active[i] - active[i - 1] <= 2:
                grp.append(active[i])
            else:
                groups.append(grp)
                grp = [active[i]]
        groups.append(grp)

        # T_tick = od začátku 1. skupiny do konce 2. skupiny (pokud existuje)
        # jinak šířka jediné skupiny
        if len(groups) >= 2:
            t13_ms = groups[1][-1] - groups[0][0] + 1
        else:
            t13_ms = groups[0][-1] - groups[0][0] + 1

        t13_s = t13_ms / 1000.0

        # Fyzikální validace: T_tick musí být v rozsahu 0.003s – 60% beat intervalu
        if not (0.003 <= t13_s <= beat_interval * 0.60):
            return None

        return t13_s

    def add_measurement(self,
                        audio_window: np.ndarray,
                        lift_angle: float,
                        bph: int,
                        is_even: bool) -> float | None:
        """
        Přidá jedno měření T_tick.
        Odd/even separace eliminuje beat error bias z výsledné amplitudy.
        Vrátí aktuální odhad amplitudy nebo None (dokud není dost dat).

        Vzorec: A = (3600 × LA) / (T_tick × π × BPH)
        Kde T_tick = průměr mediánů T_tick_even a T_tick_odd.
        """
        t13 = self.compute_t13_from_window(audio_window, bph)

        if t13 is not None:
            # Rychlá kontrola fyzikálního rozsahu amplitudy
            amp_check = (3600.0 * lift_angle) / (t13 * np.pi * bph)
            if self.AMP_MIN <= amp_check <= self.AMP_MAX:
                if is_even:
                    self._t13_even.append(t13)
                else:
                    self._t13_odd.append(t13)

        # Čekej na minimální počet měření v OBOU kanálech
        if len(self._t13_even) < 5 or len(self._t13_odd) < 5:
            return None

        # Robustní medián každého kanálu (IQR filtr 0.7×)
        def robust_med(vals: deque) -> float | None:
            arr = np.array(vals)
            if len(arr) < 3:
                return None
            q25, q75 = np.percentile(arr, 25), np.percentile(arr, 75)
            iqr = q75 - q25
            clean = arr[(arr >= q25 - 0.7 * iqr) & (arr <= q75 + 0.7 * iqr)]
            return float(np.median(clean)) if len(clean) >= 2 else float(np.median(arr))

        me = robust_med(self._t13_even)
        mo = robust_med(self._t13_odd)

        if me is None or mo is None:
            return None

        # True T_tick = průměr odd a even mediánů (eliminuje beat error bias)
        t13_true = (me + mo) / 2.0
        amp_final = (3600.0 * lift_angle) / (t13_true * np.pi * bph)

        if not (self.AMP_MIN <= amp_final <= self.AMP_MAX):
            return None

        self._amp_output.append(amp_final)

        # Výstup: medián posledních 10 hodnot (stabilní, odolný vůči skokům)
        return float(np.median(list(self._amp_output)[-10:]))


# ═══════════════════════════════════════════════════════════════════════════
#  RATE ESTIMATOR – robustní výpočet denní odchylky
#
#  Metoda:
#    – Oddělené mediány pro sudé (tick) a liché (tock) intervaly
#    – True beat interval = průměr mediánů (eliminuje beat error z výpočtu)
#    – Denní odchylka = 86400 × (nominal_interval / true_interval - 1)
#    – Stabilizace pomocí exponenciálního klouzavého průměru (EMA)
#    – Outlier rejection: zahazuje intervaly >3σ od mediánu
# ═══════════════════════════════════════════════════════════════════════════

class RateEstimator:
    """
    Robustní výpočet denní odchylky a beat error.

    Stabilizační strategie:
      – Žádný výstup dokud nemáme >= MIN_PAIRS párů tick+tock (výchozí 10)
      – Tighter outlier gate: 8% místo 15% (odmítá hrubé chyby)
      – Dvoufázové EMA: pomalé na začátku (α=0.04) → rychlejší po ustálení (α=0.10)
        přechod nastane po 30 párech – takto se číslo "usadí" bez divokých skoků
      – Robust median s 2.5σ rejection (přísnější než 3σ)
    """

    MIN_PAIRS   = 14   # min. počet párů před prvním výstupem
    MIN_HISTORY = 8    # min. hodnot v rate_history před výstupem

    def __init__(self, maxlen: int = 600):
        self._even: deque = deque(maxlen=maxlen)
        self._odd:  deque = deque(maxlen=maxlen)
        self._rate_history: deque = deque(maxlen=30)  # pro medián výstupů
        self._be_ema:   float | None = None
        self._settled = False   # příznak – přešli jsme do stabilní fáze?

    def reset(self):
        self._even.clear()
        self._odd.clear()
        self._rate_history.clear()
        self._be_ema  = None
        self._settled = False

    def _robust_median(self, data: list) -> float | None:
        if not data:
            return None
        if len(data) < 4:
            return float(np.median(data))
        arr = np.array(data)
        med = np.median(arr)
        std = np.std(arr)
        if std < 1e-9:
            return float(med)
        # 2.5-sigma rejection – přísnější než standardní 3σ
        clean = arr[np.abs(arr - med) < 2.5 * std]
        return float(np.median(clean)) if len(clean) >= 2 else float(med)

    def add_interval(self, dt: float, is_even: bool, nominal_interval: float):
        """
        Přidá interval po validaci.
        Outlier gate: max 8% odchylka od nominálního intervalu.
        To odpovídá max ±~7000 s/d odchylce – zachytí i hodně rozházené hodinky
        ale odmítne double-triggery a výpadky tiků.
        """
        if abs(dt - nominal_interval) > nominal_interval * 0.08:
            return  # mimo rozsah – zahodit

        if is_even:
            self._even.append(dt)
        else:
            self._odd.append(dt)

    def compute(self, nominal_interval: float) -> tuple[float | None, float | None]:
        """
        Vrátí (rate_s_per_day, beat_error_ms) nebo (None, None).
        Výstup je potlačen do dosažení MIN_PAIRS párů.
        """
        n_even = len(self._even)
        n_odd  = len(self._odd)

        # Čekáme na minimální počet dat v OBOU kanálech
        if n_even < self.MIN_PAIRS // 2 or n_odd < self.MIN_PAIRS // 2:
            return None, None

        me = self._robust_median(list(self._even))
        mo = self._robust_median(list(self._odd))

        if me is None or mo is None:
            return None, None

        true_interval = (me + mo) / 2.0
        if true_interval <= 0:
            return None, None

        # Surová denní odchylka [s/d]
        rate_raw = 86400.0 * (nominal_interval / true_interval - 1.0)

        # Dvoufázové EMA:
        #   fáze 1 (< 30 párů): α = 0.04 – velmi pomalé, žádné skoky
        #   fáze 2 (≥ 30 párů): α = 0.10 – rychlejší sledování změn
        n_total = n_even + n_odd
        if not self._settled and n_total >= 30:
            self._settled = True

        alpha = 0.10 if self._settled else 0.04

        # Udržujeme historii surových rate hodnot
        self._rate_history.append(rate_raw)

        # Výstup = medián posledních N surových hodnot (robustnější než EMA)
        # Dokud nemáme alespoň 5 hodnot v historii, výstup potlačíme –
        # brání divokým hodnotám na samém začátku (1.–4. výstup)
        if len(self._rate_history) < self.MIN_HISTORY:
            return None, None

        rate_out = float(np.median(list(self._rate_history)))

        # Beat error [ms]
        be_raw = abs(me - mo) * 1000.0 / 2.0
        if self._be_ema is None:
            self._be_ema = be_raw
        else:
            self._be_ema = self._be_ema * (1.0 - 0.08) + be_raw * 0.08

        return rate_out, self._be_ema

    def sample_count(self) -> int:
        return len(self._even) + len(self._odd)


# ═══════════════════════════════════════════════════════════════════════════
#  HLAVNÍ APLIKACE
# ═══════════════════════════════════════════════════════════════════════════

class TimegrapherApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurivon Watch Timegrapher - Master Architecture v3.1")
        self.resize(1600, 950)
        self.setStyleSheet(STYLESHEET)

        pg.setConfigOption('background', '#030303')
        pg.setConfigOption('foreground', '#666666')
        pg.setConfigOptions(antialias=True)

        self.sample_rate = 44100
        self.is_playing = False

        self.settings = {
            'bph': 'AUTO',
            'lift_angle': 52.0,
            'averaging_period': 600,
            'settling_time': 5,
            'device_name': '',
            'filter_mode': 'Precision (1000Hz - 6000Hz)',
            'gain': 10.0,
            'threshold': 0.150,
            'manual_threshold': False,
            'sample_rate': 'AUTO (Max. možná)',
            'tolerance_std': 'COSC (-4/+6 s/d)'
        }

        self.saved_history = []
        self.pos_data = {
            "DIAL UP (Ciferník Nahoru)": None,
            "DIAL DOWN (Ciferník Dolů)": None,
            "CROWN RIGHT (3H)": None,
            "CROWN LEFT (9H)": None,
            "CROWN UP (12H)": None,
            "CROWN DOWN (6H)": None
        }

        self.load_data()

        self.active_bph = 21600
        self.audio_data = None

        # Nové robustní estimátory
        self.amplitude_estimator = AmplitudeEstimator(self.sample_rate)
        self.rate_estimator = RateEstimator(maxlen=600)

        self.plot_data = []
        self.raw_deviations = []

        self.beat_counter = 0
        self.first_tick_time = None
        self.last_tick_time = None
        self.current_time_sec = 0.0
        self.start_time_sec = 0.0
        self.cooldown = 0
        self.scope_zoom = 1.0

        self.current_rate = 0.0
        self.current_amp = 0.0
        self.current_be = 0.0
        self.signal_quality = 100.0

        self.stream = None

        # Threshold auto-tuning state
        self._thresh_history: deque = deque(maxlen=50)
        # Amplitude window předaná z audio_callback do process_tick
        self._pending_amp_window: np.ndarray | None = None
        # Buffer pro amplitude filtr (1000-8000 Hz, bez gain)
        self._amp_audio_data: np.ndarray = np.zeros(88200)  # 2s @ 44100

        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QtWidgets.QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = QtWidgets.QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(240)
        self.sidebar.addItems([
            "TIMEGRAPHER",
            "OSCILOSKOP",
            "NASTAVENÍ",
            "POLOHY",
            "DETAILNÍ ANALÝZA",
            "SERVISNÍ PROTOKOL",
            "HISTORIE MĚŘENÍ"
        ])
        self.sidebar.setCurrentRow(0)
        self.sidebar.currentRowChanged.connect(self.switch_tab)
        main_layout.addWidget(self.sidebar)

        self.stack = QtWidgets.QStackedWidget()
        main_layout.addWidget(self.stack)

        self.setup_tab_timegrapher()
        self.setup_tab_scope()
        self.setup_tab_settings()
        self.setup_tab_positions()
        self.setup_tab_analysis()
        self.setup_tab_protocol()
        self.setup_tab_history()

        QtWidgets.QShortcut(QtGui.QKeySequence("Up"), self).activated.connect(lambda: self.adjust_threshold(0.005))
        QtWidgets.QShortcut(QtGui.QKeySequence("Down"), self).activated.connect(lambda: self.adjust_threshold(-0.005))
        QtWidgets.QShortcut(QtGui.QKeySequence("+"), self).activated.connect(lambda: self.adjust_zoom(0.8))
        QtWidgets.QShortcut(QtGui.QKeySequence("-"), self).activated.connect(lambda: self.adjust_zoom(1.25))

        self.init_audio_engine()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(50)

    # ───────────────────────────── DATA I/O ──────────────────────────────

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "settings" in data:
                        self.settings.update(data["settings"])
                    if "history" in data:
                        self.saved_history = data["history"]
            except:
                pass

    def save_data(self):
        data = {"settings": self.settings, "history": self.saved_history}
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except:
            pass

    def closeEvent(self, event):
        self.apply_settings()
        self.save_data()
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
        event.accept()

    # ─────────────────────────── UI SETUP ────────────────────────────────


    def apply_theme(self, theme_name: str):
        self.current_theme = theme_name
        self.settings['theme'] = theme_name
        t = ThemeEngine.THEMES[theme_name]
        
        self.setStyleSheet(ThemeEngine.generate_stylesheet(theme_name))
        
        # Rekonfigurace osciloskopů a grafů
        pg.setConfigOption('background', t['bg_main'])
        pg.setConfigOption('foreground', t['text_muted'])
        
        if hasattr(self, 'plot_tg'):
            self.plot_tg.setBackground(t['bg_main'])
            self.plot_audio.setBackground(t['bg_main'])
            self.plot_hist.setBackground(t['bg_main'])
            
            # Přestylování Scatter a Line grafů podle tématu
            self.scatter_even.setBrush(pg.mkBrush(t['accent_1']))
            self.scatter_odd.setBrush(pg.mkBrush(t['accent_2']))
            self.audio_curve.setPen(pg.mkPen(t['accent_1'], width=1.5))
            self.thresh_line.setPen(pg.mkPen(t['accent_2'], width=2))
            self.thresh_line_neg.setPen(pg.mkPen(t['accent_2'], width=1, style=QtCore.Qt.DashLine))
            self.marker_even.setPen(pg.mkPen(t['accent_1'], width=2))
            self.marker_odd.setPen(pg.mkPen(t['accent_2'], width=2))

            # Dynamický update popisků velkých displejů
            self.disp_rate.value_label.setStyleSheet(f"color: {t['accent_1']}; font-size: 55px; font-weight: bold; font-family: Consolas;")
            self.disp_amp.value_label.setStyleSheet(f"color: {t['accent_1']}; font-size: 55px; font-weight: bold; font-family: Consolas;")
            self.disp_be.value_label.setStyleSheet(f"color: {t['accent_1']}; font-size: 55px; font-weight: bold; font-family: Consolas;")

    def setup_tab_timegrapher(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        diag_layout = QtWidgets.QHBoxLayout()
        self.lbl_grade = QtWidgets.QLabel("HODNOCENÍ: ČEKÁM NA DATA")
        self.lbl_grade.setStyleSheet("color: #888888; font-size: 20px; font-weight: bold; letter-spacing: 1px;")
        self.lbl_sqi = QtWidgets.QLabel("SQI (Signál): ---%")
        self.lbl_sqi.setStyleSheet("color: #888888; font-size: 16px; font-weight: bold;")
        diag_layout.addWidget(self.lbl_grade)
        diag_layout.addStretch()
        diag_layout.addWidget(self.lbl_sqi)
        layout.addLayout(diag_layout)

        disp_layout = QtWidgets.QHBoxLayout()
        disp_layout.setSpacing(20)
        self.disp_rate = self.create_big_display("ODCHYLKA (S/D)", "+0.0", "#00E5FF", "Zrušeno")
        self.disp_amp  = self.create_big_display("AMPLITUDA", "---°", "#00E5FF", "Zrušeno")
        self.disp_be   = self.create_big_display("BEAT ERROR", "-.- ms", "#00E5FF", "Zrušeno")
        disp_layout.addWidget(self.disp_rate)
        disp_layout.addWidget(self.disp_amp)
        disp_layout.addWidget(self.disp_be)
        layout.addLayout(disp_layout)

        ctrl_layout = QtWidgets.QHBoxLayout()
        self.lbl_status = QtWidgets.QLabel("PŘIPRAVENO")
        self.lbl_status.setStyleSheet("color: #AAAAAA; font-size: 16px; font-weight: bold; letter-spacing: 2px;")

        self.btn_main_play = QtWidgets.QPushButton("SPUSTIT")
        self.btn_main_play.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_main_play.setFixedSize(200, 45)
        self.btn_main_play.clicked.connect(self.toggle_play)

        self.btn_main_cancel = QtWidgets.QPushButton("ZRUŠIT")
        self.btn_main_cancel.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.btn_main_cancel.setFixedSize(200, 45)
        self.btn_main_cancel.setStyleSheet(
            "background-color: #050505; border: 2px solid #FF3366; color: #FF3366; font-weight: bold; letter-spacing: 1px;")
        self.btn_main_cancel.clicked.connect(self.cancel_measurements)

        self.update_play_button_style()

        ctrl_layout.addWidget(self.lbl_status)
        ctrl_layout.addStretch()
        ctrl_layout.addWidget(self.btn_main_play)
        ctrl_layout.addSpacing(10)
        ctrl_layout.addWidget(self.btn_main_cancel)
        layout.addLayout(ctrl_layout)

        self.plot_tg = pg.PlotWidget()
        self.plot_tg.setMouseEnabled(x=False, y=False)
        self.plot_tg.hideButtons()
        self.plot_tg.setLabel('left', 'Odchylka [ms]')
        self.plot_tg.setLabel('bottom', 'Sweep Osa [s]')
        self.plot_tg.showGrid(x=True, y=True, alpha=0.2)
        self.plot_tg.getAxis('left').setPen('#333333')
        self.plot_tg.getAxis('bottom').setPen('#333333')
        self.plot_tg.setXRange(0, 60, padding=0)
        self.plot_tg.setYRange(-40, 40, padding=0)

        self.scatter_even = pg.ScatterPlotItem(size=3, pen=pg.mkPen(None), brush=pg.mkBrush(0, 229, 255, 255))
        self.scatter_odd  = pg.ScatterPlotItem(size=3, pen=pg.mkPen(None), brush=pg.mkBrush(255, 51, 102, 255))
        self.sweep_line   = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#FFFFFF', width=2, alpha=150))

        self.plot_tg.addItem(self.scatter_even)
        self.plot_tg.addItem(self.scatter_odd)
        self.plot_tg.addItem(self.sweep_line)

        layout.addWidget(self.plot_tg)
        self.stack.addWidget(w)

    def setup_tab_scope(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.setContentsMargins(40, 40, 40, 40)

        info_widget = QtWidgets.QWidget()
        info_widget.setObjectName("BorderBox")
        info_widget.setFixedHeight(60)
        ib_layout = QtWidgets.QHBoxLayout(info_widget)
        ib_layout.setContentsMargins(20, 0, 20, 0)

        lbl_info = QtWidgets.QLabel("Zkratky: [↑]/[↓] Práh detekce  |  [+]/[-] Zoom osciloskopu")
        lbl_info.setStyleSheet("color: #AAAAAA; font-size: 14px; border: none;")

        self.lbl_scope_thresh = QtWidgets.QLabel(f"PRÁH: {self.settings['threshold']:.3f}")
        self.lbl_scope_thresh.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #FF3366; letter-spacing: 1px; border: none;")

        ib_layout.addWidget(lbl_info)
        ib_layout.addStretch()
        ib_layout.addWidget(self.lbl_scope_thresh)
        layout.addWidget(info_widget)
        layout.addSpacing(15)

        self.plot_audio = pg.PlotWidget()
        self.plot_audio.setMouseEnabled(x=False, y=False)
        self.plot_audio.hideButtons()
        self.plot_audio.setYRange(-self.scope_zoom, self.scope_zoom)
        self.plot_audio.setXRange(0, 2.0, padding=0)
        self.plot_audio.showGrid(x=True, y=True, alpha=0.1)
        self.plot_audio.getAxis('left').setPen('#333333')
        self.plot_audio.getAxis('bottom').setPen('#333333')

        self.audio_curve     = self.plot_audio.plot(pen=pg.mkPen('#00E5FF', width=1))
        self.thresh_line     = pg.InfiniteLine(angle=0, movable=False, pos=self.settings['threshold'],
                                               pen=pg.mkPen('#FF3366', width=2))
        self.thresh_line_neg = pg.InfiniteLine(angle=0, movable=False, pos=-self.settings['threshold'],
                                               pen=pg.mkPen('#FF3366', width=1, style=QtCore.Qt.DashLine))
        self.plot_audio.addItem(self.thresh_line)
        self.plot_audio.addItem(self.thresh_line_neg)

        self.marker_even = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#00E5FF', width=2))
        self.marker_odd  = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen('#FF3366', width=2))
        self.plot_audio.addItem(self.marker_even)
        self.plot_audio.addItem(self.marker_odd)

        layout.addWidget(self.plot_audio)
        self.stack.addWidget(w)

    def setup_tab_settings(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.setContentsMargins(50, 50, 50, 50)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(40)

        gb_watch = QtWidgets.QGroupBox("PARAMETRY HODINEK")
        form_w = QtWidgets.QFormLayout(gb_watch)
        form_w.setContentsMargins(20, 30, 20, 20)
        form_w.setSpacing(20)

        self.inp_bph = QtWidgets.QComboBox()
        self.inp_bph.addItems(["AUTO", "14400", "18000", "21600", "28800", "36000"])
        self.inp_bph.setCurrentText(str(self.settings.get('bph', 'AUTO')))
        self.inp_bph.currentTextChanged.connect(self.apply_settings)

        self.inp_lift = QtWidgets.QDoubleSpinBox()
        self.inp_lift.setRange(30.0, 70.0)
        self.inp_lift.setValue(float(self.settings.get('lift_angle', 52.0)))
        self.inp_lift.setSingleStep(0.5)
        self.inp_lift.valueChanged.connect(self.apply_settings)

        self.inp_std = QtWidgets.QComboBox()
        self.inp_std.addItems(["COSC (-4/+6 s/d)", "Vintage (-15/+15 s/d)", "Standard (-10/+10 s/d)"])
        self.inp_std.setCurrentText(self.settings.get('tolerance_std', 'COSC (-4/+6 s/d)'))
        self.inp_std.currentTextChanged.connect(self.apply_settings)

        form_w.addRow("Beat Rate (BPH):", self.inp_bph)
        form_w.addRow("Lift Angle (°):", self.inp_lift)
        form_w.addRow("Standard Kvality:", self.inp_std)

        gb_test = QtWidgets.QGroupBox("MĚŘÍCÍ CYKLUS")
        form_t = QtWidgets.QFormLayout(gb_test)
        form_t.setContentsMargins(20, 30, 20, 20)
        form_t.setSpacing(20)

        self.inp_avg = QtWidgets.QSpinBox()
        self.inp_avg.setRange(10, 3600)
        self.inp_avg.setValue(int(self.settings.get('averaging_period', 600)))
        self.inp_avg.valueChanged.connect(self.apply_settings)

        self.inp_settle = QtWidgets.QSpinBox()
        self.inp_settle.setRange(0, 60)
        self.inp_settle.setValue(int(self.settings.get('settling_time', 5)))
        self.inp_settle.valueChanged.connect(self.apply_settings)

        self.chk_manual_thresh = QtWidgets.QCheckBox("Manuální nastavení prahu (Zakáže Auto-Tuning)")
        self.chk_manual_thresh.setChecked(bool(self.settings.get('manual_threshold', False)))
        self.chk_manual_thresh.stateChanged.connect(self.apply_settings)

        form_t.addRow("Averaging Period [s]:", self.inp_avg)
        form_t.addRow("Settling Time [s]:", self.inp_settle)
        form_t.addRow("", self.chk_manual_thresh)

        gb_audio = QtWidgets.QGroupBox("AUDIO A HARDWARE")
        form_a = QtWidgets.QFormLayout(gb_audio)
        form_a.setContentsMargins(20, 30, 20, 20)
        form_a.setSpacing(20)

        self.inp_device = QtWidgets.QComboBox()
        try:
            devices = sd.query_devices()
            for i, d in enumerate(devices):
                if d['max_input_channels'] > 0:
                    self.inp_device.addItem(f"{d['name']}", i)
        except:
            self.inp_device.addItem("Výchozí systémové zařízení", None)

        saved_device = self.settings.get('device_name', '')
        idx = self.inp_device.findText(saved_device)
        if idx >= 0:
            self.inp_device.setCurrentIndex(idx)
        self.inp_device.currentIndexChanged.connect(self.restart_audio)

        self.inp_filter = QtWidgets.QComboBox()
        self.inp_filter.addItems([
            "Precision (1000Hz - 6000Hz)",
            "Narrow (800Hz - 8kHz)",
            "Broad (100Hz - 10kHz)",
            "None (Raw)"
        ])
        self.inp_filter.setCurrentText(self.settings.get('filter_mode', 'Precision (1000Hz - 6000Hz)'))
        self.inp_filter.currentTextChanged.connect(self.apply_settings)

        self.inp_samplerate = QtWidgets.QComboBox()
        self.inp_samplerate.addItems(["AUTO (Max. možná)", "44100", "48000", "96000", "192000"])
        self.inp_samplerate.setCurrentText(self.settings.get('sample_rate', 'AUTO (Max. možná)'))
        self.inp_samplerate.currentTextChanged.connect(self.restart_audio)

        self.slider_gain = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider_gain.setRange(1, 50)
        self.slider_gain.setValue(int(self.settings.get('gain', 10.0)))
        self.slider_gain.valueChanged.connect(self.apply_settings)

        self.lbl_rate_info = QtWidgets.QLabel("Aktivní vzorkování: ---")
        self.lbl_rate_info.setStyleSheet("color: #00FF66; font-weight: bold;")

        form_a.addRow("Vstupní Zařízení:", self.inp_device)
        form_a.addRow("Digitální Filtr:", self.inp_filter)
        form_a.addRow("Vzorkovací frekvence:", self.inp_samplerate)
        form_a.addRow("Zesílení Signálu:", self.slider_gain)
        form_a.addRow("Status Audia:", self.lbl_rate_info)

        grid.addWidget(gb_watch, 0, 0)
        grid.addWidget(gb_test, 1, 0)
        grid.addWidget(gb_audio, 0, 1, 2, 1)

        layout.addLayout(grid)
        layout.addStretch()
        self.stack.addWidget(w)

    def setup_tab_positions(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.setContentsMargins(40, 40, 40, 40)

        self.pos_labels = {}
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(20)
        positions = list(self.pos_data.keys())

        for i, pos_name in enumerate(positions):
            gb = QtWidgets.QGroupBox(pos_name)
            vbox = QtWidgets.QVBoxLayout(gb)
            vbox.setContentsMargins(20, 20, 20, 20)

            lbl = QtWidgets.QLabel("NEZAZNAMENÁNO")
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 14px; color: #666666; font-weight: bold;")

            btn = QtWidgets.QPushButton("ULOŽIT DO POZICE")
            btn.setStyleSheet(
                "background-color: #0A0A0A; border: 1px solid #333333; color: #AAAAAA; padding: 5px;")
            btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            btn.clicked.connect(lambda checked, p=pos_name: self.save_position(p))

            vbox.addWidget(lbl)
            vbox.addSpacing(10)
            vbox.addWidget(btn)

            self.pos_labels[pos_name] = lbl
            grid.addWidget(gb, i // 3, i % 3)

        layout.addLayout(grid)

        btn_layout = QtWidgets.QHBoxLayout()
        btn_clear_pos = QtWidgets.QPushButton("VYMAZAT VŠECHNY POLOHY")
        btn_clear_pos.setFixedSize(300, 40)
        btn_clear_pos.setStyleSheet(
            "background-color: #050505; border: 1px solid #FF3366; color: #FF3366;")
        btn_clear_pos.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn_clear_pos.clicked.connect(self.clear_positions)

        btn_layout.addWidget(btn_clear_pos)
        btn_layout.addStretch()
        layout.addSpacing(20)
        layout.addLayout(btn_layout)
        layout.addStretch()

        self.stack.addWidget(w)

    def setup_tab_analysis(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.setContentsMargins(40, 40, 40, 40)

        header_layout = QtWidgets.QHBoxLayout()
        lbl_title = QtWidgets.QLabel("DETAILNÍ EXPERTNÍ DIAGNOSTIKA")
        lbl_title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #00E5FF; letter-spacing: 2px;")
        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        layout.addSpacing(20)

        grid = QtWidgets.QGridLayout()
        grid.setSpacing(30)

        self.box_state = QtWidgets.QGroupBox("METRIKY A TREND")
        state_layout = QtWidgets.QVBoxLayout(self.box_state)
        state_layout.setSpacing(15)
        self.lbl_ana_drift = QtWidgets.QLabel("Trend Grafu: Čekám na data")
        self.lbl_ana_var   = QtWidgets.QLabel("Stabilita (Rozptyl): Čekám na data")
        self.lbl_ana_sqi   = QtWidgets.QLabel("Kvalita Signálu (SQI): Čekám na data")
        for lbl in [self.lbl_ana_drift, self.lbl_ana_var, self.lbl_ana_sqi]:
            lbl.setStyleSheet("color: #FFFFFF; font-size: 14px;")
            state_layout.addWidget(lbl)
        grid.addWidget(self.box_state, 0, 0)

        self.box_errors = QtWidgets.QGroupBox("DIAGNOSTIKA KROKU A ZÁVAD")
        errors_layout = QtWidgets.QVBoxLayout(self.box_errors)
        errors_layout.setSpacing(15)
        self.lbl_err_esc   = QtWidgets.QLabel("-")
        self.lbl_err_amp   = QtWidgets.QLabel("-")
        self.lbl_err_be    = QtWidgets.QLabel("-")
        self.lbl_err_noise = QtWidgets.QLabel("-")
        for lbl in [self.lbl_err_esc, self.lbl_err_amp, self.lbl_err_be, self.lbl_err_noise]:
            lbl.setStyleSheet("color: #FFFFFF; font-size: 14px;")
            errors_layout.addWidget(lbl)
        grid.addWidget(self.box_errors, 0, 1)

        self.box_pos = QtWidgets.QGroupBox("ANALÝZA POLOH A TĚŽIŠTĚ")
        pos_layout = QtWidgets.QVBoxLayout(self.box_pos)
        pos_layout.setSpacing(15)
        self.lbl_ana_delta = QtWidgets.QLabel("Delta: Nedostatek poloh k analýze.")
        self.lbl_ana_heavy = QtWidgets.QLabel("Heavy Spot (Těžké místo): Změřte vertikální polohy.")
        for lbl in [self.lbl_ana_delta, self.lbl_ana_heavy]:
            lbl.setStyleSheet("color: #FFFFFF; font-size: 14px;")
            pos_layout.addWidget(lbl)
        grid.addWidget(self.box_pos, 1, 0, 1, 2)

        self.box_action = QtWidgets.QGroupBox("⚙️ ZÁVĚR A KROKOVÝ PLÁN (AUTO-ANALÝZA)")
        self.box_action.setStyleSheet(
            "QGroupBox { border: 1px solid #00E5FF; } QGroupBox::title { color: #00E5FF; }")
        action_layout = QtWidgets.QVBoxLayout(self.box_action)
        self.lbl_action_plan = QtWidgets.QLabel("Pro vygenerování plánu sbírejte data z měření.")
        self.lbl_action_plan.setWordWrap(True)
        self.lbl_action_plan.setStyleSheet(
            "font-size: 15px; font-weight: normal; color: #FFFFFF; line-height: 1.5;")
        action_layout.addWidget(self.lbl_action_plan)
        grid.addWidget(self.box_action, 2, 0, 1, 2)

        layout.addLayout(grid)
        layout.addStretch()
        self.stack.addWidget(w)

    def setup_tab_protocol(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.setContentsMargins(40, 40, 40, 40)

        header_layout = QtWidgets.QHBoxLayout()
        lbl_title = QtWidgets.QLabel("SERVISNÍ PROTOKOL KLIENTA")
        lbl_title.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #00E5FF; letter-spacing: 2px;")

        btn_export = QtWidgets.QPushButton("EXPORTOVAT DO PDF A ULOŽIT")
        btn_export.setFixedSize(300, 45)
        btn_export.setStyleSheet(
            "background-color: #050505; border: 2px solid #00FF66; color: #00FF66; font-weight: bold; letter-spacing: 1px;")
        btn_export.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        btn_export.clicked.connect(self.export_protocol)

        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(btn_export)
        layout.addLayout(header_layout)
        layout.addSpacing(20)

        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        left_widget = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)

        gb_auto = QtWidgets.QGroupBox("NAMĚŘENÁ DATA A DIAGNOSTIKA (AUTOMATICKY)")
        gb_auto_layout = QtWidgets.QVBoxLayout(gb_auto)

        self.txt_protocol_auto = QtWidgets.QTextEdit()
        self.txt_protocol_auto.setObjectName("ProtocolData")
        self.txt_protocol_auto.setReadOnly(True)
        gb_auto_layout.addWidget(self.txt_protocol_auto)
        left_layout.addWidget(gb_auto)
        split.addWidget(left_widget)

        right_widget = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)

        gb_input = QtWidgets.QGroupBox("IDENTIFIKACE A SERVISNÍ ZÁZNAMY")
        form_layout = QtWidgets.QFormLayout(gb_input)
        form_layout.setContentsMargins(20, 30, 20, 20)
        form_layout.setSpacing(15)

        self.inp_client      = QtWidgets.QLineEdit()
        self.inp_watch       = QtWidgets.QLineEdit()
        self.inp_serial      = QtWidgets.QLineEdit()
        self.inp_service_num = QtWidgets.QLineEdit()

        self.txt_state_before = QtWidgets.QTextEdit()
        self.txt_case_cond    = QtWidgets.QTextEdit()
        self.txt_work         = QtWidgets.QTextEdit()
        self.txt_parts        = QtWidgets.QTextEdit()

        self.txt_state_before.setFixedHeight(60)
        self.txt_case_cond.setFixedHeight(60)
        self.txt_work.setFixedHeight(100)
        self.txt_parts.setFixedHeight(60)

        form_layout.addRow("Zákazník:", self.inp_client)
        form_layout.addRow("Značka / Model:", self.inp_watch)
        form_layout.addRow("Sériové číslo / Kalibr:", self.inp_serial)
        form_layout.addRow("Číslo servisu:", self.inp_service_num)
        form_layout.addRow("Stav strojku před servisem:", self.txt_state_before)
        form_layout.addRow("Stav/Renovace pouzdra:", self.txt_case_cond)
        form_layout.addRow("Provedené práce a servis:", self.txt_work)
        form_layout.addRow("Vyměněné díly:", self.txt_parts)

        right_layout.addWidget(gb_input)
        split.addWidget(right_widget)
        split.setSizes([700, 800])
        layout.addWidget(split)

        self.stack.addWidget(w)

    def setup_tab_history(self):
        w = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(w)
        layout.setContentsMargins(40, 40, 40, 40)

        lbl_title = QtWidgets.QLabel("DATABÁZE MĚŘENÍ A PROTOKOLŮ")
        lbl_title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: #FFFFFF; letter-spacing: 1px;")
        layout.addWidget(lbl_title)
        layout.addSpacing(10)

        split = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        self.list_history = QtWidgets.QListWidget()
        self.list_history.setObjectName("HistoryList")
        self.list_history.currentRowChanged.connect(self.load_history_detail)
        split.addWidget(self.list_history)

        detail_widget = QtWidgets.QWidget()
        detail_layout = QtWidgets.QVBoxLayout(detail_widget)
        detail_layout.setContentsMargins(20, 0, 0, 0)

        self.lbl_hist_name    = QtWidgets.QLabel("Vyberte záznam")
        self.lbl_hist_name.setStyleSheet("font-size: 24px; font-weight: bold; color: #00E5FF;")
        detail_layout.addWidget(self.lbl_hist_name)

        self.lbl_hist_metrics = QtWidgets.QLabel("")
        self.lbl_hist_metrics.setStyleSheet("font-size: 16px; color: #FFFFFF;")
        detail_layout.addWidget(self.lbl_hist_metrics)

        self.txt_hist_analysis = QtWidgets.QTextEdit()
        self.txt_hist_analysis.setObjectName("AnalysisPanel")
        self.txt_hist_analysis.setReadOnly(True)
        self.txt_hist_analysis.setFixedHeight(280)
        detail_layout.addWidget(self.txt_hist_analysis)

        self.plot_hist = pg.PlotWidget()
        self.plot_hist.setMouseEnabled(x=False, y=False)
        self.plot_hist.hideButtons()
        self.plot_hist.showGrid(x=True, y=True, alpha=0.2)
        self.plot_hist.getAxis('left').setPen('#333333')
        self.plot_hist.getAxis('bottom').setPen('#333333')
        self.plot_hist.setYRange(-40, 40, padding=0)

        self.hist_scatter_even = pg.ScatterPlotItem(size=3, pen=pg.mkPen(None),
                                                    brush=pg.mkBrush(0, 229, 255, 255))
        self.hist_scatter_odd  = pg.ScatterPlotItem(size=3, pen=pg.mkPen(None),
                                                    brush=pg.mkBrush(255, 51, 102, 255))
        self.plot_hist.addItem(self.hist_scatter_even)
        self.plot_hist.addItem(self.hist_scatter_odd)
        detail_layout.addWidget(self.plot_hist)

        split.addWidget(detail_widget)
        split.setSizes([300, 900])
        layout.addWidget(split)

        btn_clear_hist = QtWidgets.QPushButton("VYMAZAT VŠECHNY ZÁZNAMY")
        btn_clear_hist.setFixedSize(250, 40)
        btn_clear_hist.setStyleSheet(
            "background-color: #050505; border: 1px solid #FF3366; color: #FF3366;")
        btn_clear_hist.clicked.connect(self.clear_current_history)
        layout.addWidget(btn_clear_hist)

        self.stack.addWidget(w)
        self.populate_history_list()

    def create_big_display(self, title, val, color, default_info="Zatím bez dat"):
        gb = QtWidgets.QGroupBox(title)
        l  = QtWidgets.QVBoxLayout(gb)
        l.setContentsMargins(20, 30, 20, 20)

        lbl = QtWidgets.QLabel(val)
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        lbl.setStyleSheet(
            f"font-size: 55px; font-weight: bold; font-family: Consolas; color: {color};")

        info = QtWidgets.QLabel(default_info)
        info.setAlignment(QtCore.Qt.AlignCenter)
        info.setStyleSheet("color: #777777; font-size: 13px; font-weight: bold;")

        l.addWidget(lbl)
        l.addWidget(info)
        gb.value_label = lbl
        gb.info_label  = info
        return gb

    def update_play_button_style(self):
        if self.is_playing:
            self.btn_main_play.setText("PAUZA")
            self.btn_main_play.setStyleSheet(
                "background-color: #050505; border: 2px solid #FFB300; color: #FFB300; font-weight: bold; letter-spacing: 2px;")
        else:
            self.btn_main_play.setText("SPUSTIT")
            self.btn_main_play.setStyleSheet(
                "background-color: #050505; border: 2px solid #00E5FF; color: #00E5FF; font-weight: bold; letter-spacing: 2px;")

    def switch_tab(self, index):
        self.stack.setCurrentIndex(index)
        if index == 4: self.update_analysis_tab()
        if index == 5: self.update_protocol_tab()

    def populate_history_list(self):
        self.list_history.clear()
        for rec in reversed(self.saved_history):
            self.list_history.addItem(
                f"[{rec['time']}] {rec.get('client', rec.get('name', ''))}")

    def load_history_detail(self, index):
        if index < 0 or index >= len(self.saved_history):
            return
        rec = self.saved_history[len(self.saved_history) - 1 - index]

        self.lbl_hist_name.setText(rec.get('watch_model', rec.get('name', '')))
        self.lbl_hist_metrics.setText(
            f"Odchylka: {rec['rate']:+.1f} s/d   |   "
            f"Amplituda: {int(rec['amp'])}°   |   "
            f"Beat Error: {rec['be']:.1f} ms")

        diag = rec.get('full_diagnostics', {})
        if isinstance(diag, dict) and diag:
            html = f"""
            <h3 style='color:#00E5FF; margin-bottom: 2px;'>SERVISNÍ ÚKONY</h3>
            <p style='margin-top: 0px;'>
                <b>Zákazník:</b> {rec.get('client', '-')}<br>
                <b>Práce:</b> {rec.get('work_done', '-')}<br>
                <b>Díly:</b> {rec.get('parts', '-')}
            </p>
            <h3 style='color:#00E5FF; margin-bottom: 2px;'>TECHNICKÁ DIAGNOSTIKA</h3>
            <p style='margin-top: 0px;'>
                {diag.get('drift', '')}<br>
                {diag.get('err_esc', '')}<br>
                {diag.get('pos_heavy', '')}
            </p>
            """
            self.txt_hist_analysis.setHtml(html)
        else:
            self.txt_hist_analysis.setPlainText("Starší formát bez detailů.")

        if 'plot_even_x' in rec and len(rec['plot_even_x']) > 0:
            self.hist_scatter_even.setData(x=rec['plot_even_x'], y=rec['plot_even_y'])
            self.hist_scatter_odd.setData(x=rec['plot_odd_x'], y=rec['plot_odd_y'])
        else:
            self.hist_scatter_even.clear()
            self.hist_scatter_odd.clear()

    def clear_current_history(self):
        self.saved_history.clear()
        self.populate_history_list()
        self.save_data()

    # ─────────────────────── THRESHOLD & ZOOM ────────────────────────────

    def adjust_threshold(self, amount):
        if self.stack.currentIndex() != 1:
            return
        if not self.settings.get('manual_threshold', False):
            return
        new_val = max(0.005, self.settings['threshold'] + amount)
        self.settings['threshold'] = new_val
        self.thresh_line.setValue(new_val)
        self.thresh_line_neg.setValue(-new_val)
        mode_text = "[MANUÁL]" if self.settings.get('manual_threshold', False) else "[AUTO]"
        self.lbl_scope_thresh.setText(f"PRÁH {mode_text}: {new_val:.3f}")

    def adjust_zoom(self, multiplier):
        if self.stack.currentIndex() != 1:
            return
        self.scope_zoom *= multiplier
        self.scope_zoom = max(0.02, min(self.scope_zoom, 5.0))
        self.plot_audio.setYRange(-self.scope_zoom, self.scope_zoom)

    # ─────────────────────── PROTOCOL & EXPORT ───────────────────────────

    def update_protocol_tab(self):
        self.update_analysis_tab()
        rates = [d['rate'] for d in self.pos_data.values() if d is not None]
        delta_val = (f"{max(rates) - min(rates):.1f} s/d"
                     if len(rates) >= 2 else "Měřeno pouze v 1 poloze")

        html = f"""
        <h2 style='color:#00E5FF; border-bottom: 1px solid #333; padding-bottom: 5px;'>
            1. SOUHRNNÉ METRIKY CHODU</h2>
        <table width='100%'>
            <tr><td width='60%'><b>Průměrná odchylka (Rate):</b></td>
                <td>{self.current_rate:+.1f} s/d</td></tr>
            <tr><td><b>Amplituda kroku:</b></td>
                <td>{int(self.current_amp)}°</td></tr>
            <tr><td><b>Chyba souměrnosti (Beat Error):</b></td>
                <td>{self.current_be:.1f} ms</td></tr>
            <tr><td><b>Rozptyl v polohách (Delta):</b></td>
                <td>{delta_val}</td></tr>
            <tr><td><b>Frekvence stroje:</b></td>
                <td>{self.active_bph} BPH</td></tr>
        </table>

        <h2 style='color:#00E5FF; border-bottom: 1px solid #333; padding-bottom: 5px; margin-top: 15px;'>
            2. DIAGNOSTIKA ÚSTROJÍ</h2>
        <p>{self.lbl_err_esc.text()}<br>
           {self.lbl_err_amp.text()}<br>
           {self.lbl_err_be.text()}<br>
           {self.lbl_ana_heavy.text()}</p>

        <h2 style='color:#00E5FF; border-bottom: 1px solid #333; padding-bottom: 5px; margin-top: 15px;'>
            3. DETAILNÍ MĚŘENÍ POLOH</h2>
        <table width='100%' cellspacing='0' cellpadding='4' style='border: 1px solid #333;'>
            <tr style='background-color: #1A1A1A;'>
                <th style='text-align: left; padding-left: 5px;'>Poloha</th>
                <th style='text-align: center;'>Odchylka [s/d]</th>
                <th style='text-align: center;'>Amplituda [°]</th>
                <th style='text-align: center;'>B.E. [ms]</th>
            </tr>
        """
        for pos_name, data in self.pos_data.items():
            if data is not None:
                html += (f"<tr><td style='padding-left: 5px;'>{pos_name}</td>"
                         f"<td style='text-align: center;'>{data['rate']:+.1f}</td>"
                         f"<td style='text-align: center;'>{int(data['amp'])}</td>"
                         f"<td style='text-align: center;'>{data['be']:.1f}</td></tr>")
            else:
                html += (f"<tr><td style='padding-left: 5px;'>{pos_name}</td>"
                         f"<td colspan='3' style='text-align: center; color: #888;'>Neměřeno</td></tr>")

        html += "</table>"
        self.txt_protocol_auto.setHtml(html)

    def export_protocol(self):
        client      = self.inp_client.text().strip() or "Neznámý Zákazník"
        watch       = self.inp_watch.text().strip() or "Neznámé Hodinky"
        serial      = self.inp_serial.text().strip() or "N/A"
        service_num = self.inp_service_num.text().strip() or "N/A"

        rates = [d['rate'] for d in self.pos_data.values() if d is not None]
        delta_val = (f"{max(rates) - min(rates):.1f} s/d"
                     if len(rates) >= 2 else "Neměřeno")

        diag_dict = {
            'drift':     self.lbl_ana_drift.text(),
            'err_esc':   self.lbl_err_esc.text(),
            'pos_heavy': self.lbl_ana_heavy.text()
        }

        s_even_x, s_even_y, s_odd_x, s_odd_y = [], [], [], []
        if self.first_tick_time and self.plot_data:
            for pt in self.plot_data[-200:]:
                x = (pt[0] - self.first_tick_time) % 60.0
                y = ((pt[1] + 40.0) % 80.0) - 40.0
                if pt[2]:
                    s_even_x.append(x); s_even_y.append(y)
                else:
                    s_odd_x.append(x);  s_odd_y.append(y)

        record = {
            "time":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "client":      client,
            "watch_model": watch,
            "serial":      serial,
            "service_num": service_num,
            "state_before": self.txt_state_before.toPlainText(),
            "case_cond":   self.txt_case_cond.toPlainText(),
            "work_done":   self.txt_work.toPlainText(),
            "parts":       self.txt_parts.toPlainText(),
            "rate":        self.current_rate,
            "amp":         self.current_amp,
            "be":          self.current_be,
            "delta":       delta_val,
            "full_diagnostics": diag_dict,
            "plot_even_x": s_even_x, "plot_even_y": s_even_y,
            "plot_odd_x":  s_odd_x,  "plot_odd_y":  s_odd_y
        }
        self.saved_history.append(record)
        self.populate_history_list()
        self.save_data()

        html_pdf = f"""
        <html>
        <head>
        <style>
            body {{ font-family: 'Helvetica', 'Arial', sans-serif; color: #000; font-size: 10pt; line-height: 1.4; }}
            h1 {{ color: #000; font-size: 18pt; font-weight: bold; border-bottom: 1.5pt solid #000; padding-bottom: 4pt; margin-bottom: 15pt; }}
            h2 {{ color: #333; font-size: 12pt; margin-top: 20pt; border-bottom: 0.5pt solid #CCC; padding-bottom: 2pt; font-weight: bold; text-transform: uppercase; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 8pt; font-size: 10pt; }}
            th {{ background-color: #EEEEEE; text-align: left; padding: 6pt; border: 0.5pt solid #DDD; font-weight: bold; }}
            td {{ padding: 6pt; border: 0.5pt solid #DDD; }}
            .footer {{ font-size: 8pt; color: #777; margin-top: 40pt; text-align: center; border-top: 0.5pt solid #EEE; padding-top: 8pt; }}
            .important {{ font-weight: bold; font-size: 11pt; }}
        </style>
        </head>
        <body>
        <h1>AURIVON <span style='color: #777; font-size: 14pt; font-weight: normal;'>| LABORATORNÍ SERVISNÍ PROTOKOL</span></h1>

        <h2>IDENTIFIKACE ZAKÁZKY</h2>
        <table>
            <tr><th width='30%'>Datum generování:</th><td width='70%'>{record['time']}</td></tr>
            <tr><th>Číslo servisu:</th><td>{service_num}</td></tr>
            <tr><th>Zákazník:</th><td>{client}</td></tr>
            <tr><th>Značka / Model:</th><td>{watch}</td></tr>
            <tr><th>Sériové číslo / Kalibr:</th><td>{serial}</td></tr>
        </table>

        <h2>DIAGNOSTIKA CHODU (ZÁKLADNÍ METRIKY)</h2>
        <table>
            <tr><th width='25%'>Odchylka (Rate):</th>
                <td width='25%' class='important'>{self.current_rate:+.1f} s/d</td>
                <th width='25%'>Amplituda:</th>
                <td width='25%' class='important'>{int(self.current_amp)}°</td></tr>
            <tr><th>Beat Error:</th>
                <td class='important'>{self.current_be:.1f} ms</td>
                <th>Frekvence stroje:</th>
                <td>{self.active_bph} BPH</td></tr>
        </table>

        <h2>ANALÝZA POLOH (POZICIONÁLNÍ ODCHYLKY)</h2>
        <table>
            <tr><th width='40%'>Poloha</th><th width='20%'>Odchylka [s/d]</th>
                <th width='20%'>Amplituda [°]</th><th width='20%'>Beat Error [ms]</th></tr>
        """
        for pos_name, data in self.pos_data.items():
            if data is not None:
                html_pdf += (f"<tr><td>{pos_name}</td><td>{data['rate']:+.1f}</td>"
                             f"<td>{int(data['amp'])}</td><td>{data['be']:.1f}</td></tr>")
            else:
                html_pdf += (f"<tr><td>{pos_name}</td>"
                             f"<td colspan='3' style='color:#888;'>Neměřeno</td></tr>")

        html_pdf += f"""
        </table>
        <p><b>Delta (Rozptyl maximální chyby mezi polohami):</b> {delta_val}</p>

        <h2>SERVISNÍ ZPRÁVA A VÝKON</h2>
        <table>
            <tr><th width='30%'>Stav stroje před servisem:</th>
                <td width='70%'>{self.txt_state_before.toPlainText().replace(chr(10), '<br>') or '-'}</td></tr>
            <tr><th>Stav / Renovace pouzdra:</th>
                <td>{self.txt_case_cond.toPlainText().replace(chr(10), '<br>') or '-'}</td></tr>
            <tr><th>Provedené práce a servis:</th>
                <td>{self.txt_work.toPlainText().replace(chr(10), '<br>') or '-'}</td></tr>
            <tr><th>Vyměněné díly:</th>
                <td>{self.txt_parts.toPlainText().replace(chr(10), '<br>') or '-'}</td></tr>
            <tr><th>Závěr a diagnostika:</th>
                <td>{self.lbl_action_plan.text().replace(chr(10), '<br>')}</td></tr>
        </table>

        <div class='footer'>
            Vygenerováno certifikovaným laboratorním systémem Aurivon Master Architecture.<br>
            Tento dokument slouží jako potvrzení o provedeném měření a servisu hodinek.
        </div>
        </body>
        </html>
        """

        filename = (f"Aurivon_Protokol_{client.replace(' ', '_')}_"
                    f"{datetime.now().strftime('%Y%m%d_%H%M')}.pdf")

        try:
            printer = QtPrintSupport.QPrinter(QtPrintSupport.QPrinter.ScreenResolution)
            printer.setOutputFormat(QtPrintSupport.QPrinter.PdfFormat)
            printer.setOutputFileName(filename)
            printer.setPageMargins(15, 15, 15, 15, QtPrintSupport.QPrinter.Millimeter)

            doc = QtGui.QTextDocument()
            doc.setHtml(html_pdf)
            doc.print_(printer)

            QtWidgets.QMessageBox.information(
                self, "Exportováno",
                f"PDF Protokol byl úspěšně vygenerován a uložen jako:\n\n{filename}")
        except Exception as e:
            QtWidgets.QMessageBox.warning(
                self, "Chyba Exportu",
                f"Nepodařilo se uložit PDF. Zkontrolujte práva k zápisu.\n{str(e)}")

    # ─────────────────────────── SETTINGS ────────────────────────────────

    def apply_settings(self):
        self.settings['bph'] = self.inp_bph.currentText()
        if self.settings['bph'] != 'AUTO':
            self.active_bph = int(self.settings['bph'])
        self.settings['lift_angle']       = self.inp_lift.value()
        self.settings['averaging_period'] = self.inp_avg.value()
        self.settings['settling_time']    = self.inp_settle.value()
        self.settings['device_name']      = self.inp_device.currentText()
        self.settings['gain']             = self.slider_gain.value()
        self.settings['tolerance_std']    = self.inp_std.currentText()
        self.settings['manual_threshold'] = self.chk_manual_thresh.isChecked()

        if self.settings.get('filter_mode') != self.inp_filter.currentText():
            self.settings['filter_mode'] = self.inp_filter.currentText()
            self.setup_filters()

    def setup_filters(self):
        mode = self.settings['filter_mode']
        if "Precision" in mode:
            self.sos = signal.butter(4, [1000, 6000], btype='bandpass', fs=self.sample_rate, output='sos')
        elif "Narrow" in mode:
            self.sos = signal.butter(4, [800, 8000],  btype='bandpass', fs=self.sample_rate, output='sos')
        elif "Broad" in mode:
            self.sos = signal.butter(4, [100, 10000], btype='bandpass', fs=self.sample_rate, output='sos')
        else:
            self.sos = None

        if self.sos is not None:
            self.zi = signal.sosfilt_zi(self.sos)
        else:
            self.zi = None

    # ─────────────────────────── AUDIO ENGINE ────────────────────────────

    def init_audio_engine(self):
        device_idx   = self.inp_device.currentData() if hasattr(self, 'inp_device') else None
        desired_rate = (self.inp_samplerate.currentText()
                        if hasattr(self, 'inp_samplerate')
                        else self.settings.get('sample_rate', 'AUTO'))

        try:
            if "AUTO" in desired_rate:
                dev_info = sd.query_devices(device_idx, 'input')
                max_rate = int(dev_info['default_samplerate'])
                if   max_rate >= 192000: self.sample_rate = 192000
                elif max_rate >= 96000:  self.sample_rate = 96000
                elif max_rate >= 48000:  self.sample_rate = 48000
                else:                    self.sample_rate = 44100
            else:
                self.sample_rate = int(desired_rate)
        except:
            self.sample_rate = 44100

        self.lbl_rate_info.setText(f"Aktivní vzorkování: {self.sample_rate} Hz")
        self.audio_data = np.zeros(self.sample_rate * 2)
        self._amp_audio_data = np.zeros(self.sample_rate * 2)

        # Aktualizujeme AmplitudeEstimator s novým sample_rate
        self.amplitude_estimator = AmplitudeEstimator(self.sample_rate)
        self.amplitude_estimator.setup_amp_filter(self.sample_rate)

        self.setup_filters()
        self.start_audio_stream()

    def restart_audio(self, _=None):
        self.apply_settings()
        self.settings['sample_rate'] = self.inp_samplerate.currentText()
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
        self.init_audio_engine()

    def start_audio_stream(self):
        device_idx = self.inp_device.currentData() if hasattr(self, 'inp_device') else None
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                device=device_idx,
                callback=self.audio_callback
            )
            self.stream.start()
        except Exception as e:
            self.lbl_rate_info.setText(f"Chyba: {self.sample_rate} Hz nepodporováno.")
            self.lbl_rate_info.setStyleSheet("color: #FF3366; font-weight: bold;")

    # ─────────────────────────── CONTROLS ────────────────────────────────

    def toggle_play(self):
        self.is_playing = not self.is_playing
        self.update_play_button_style()
        if self.is_playing:
            self.start_time_sec = self.current_time_sec
            lbl = ("STABILIZACE..." if self.settings['settling_time'] > 0 else "MĚŘENÍ PROBÍHÁ")
            self.lbl_status.setText(lbl)
            self.lbl_status.setStyleSheet(
                "color: #00E5FF; font-size: 16px; font-weight: bold; letter-spacing: 2px;")
        else:
            self.lbl_status.setText("POZASTAVENO")
            self.lbl_status.setStyleSheet(
                "color: #FFB300; font-size: 16px; font-weight: bold; letter-spacing: 2px;")

    def cancel_measurements(self):
        self.is_playing = False
        self.update_play_button_style()

        self.plot_data.clear()
        self.raw_deviations.clear()
        self.amplitude_estimator.reset()
        self.rate_estimator.reset()
        self._thresh_history.clear()
        self._pending_amp_window = None

        self.beat_counter    = 0
        self.first_tick_time = None
        self.last_tick_time  = None
        self.current_rate    = 0.0
        self.current_amp     = 0.0
        self.current_be      = 0.0

        self.scatter_even.clear()
        self.scatter_odd.clear()

        grey = "color: #444444; font-size: 55px; font-weight: bold; font-family: Consolas;"
        self.disp_rate.value_label.setText("+0.0")
        self.disp_rate.value_label.setStyleSheet(grey)
        self.disp_amp.value_label.setText("---°")
        self.disp_amp.value_label.setStyleSheet(grey)
        self.disp_be.value_label.setText("-.- ms")
        self.disp_be.value_label.setStyleSheet(grey)

        self.disp_rate.info_label.setText("Zrušeno")
        self.disp_amp.info_label.setText("Zrušeno")
        self.disp_be.info_label.setText("Zrušeno")

        self.lbl_grade.setText("HODNOCENÍ: ZRUŠENO")
        self.lbl_grade.setStyleSheet("color: #888888; font-size: 20px; font-weight: bold;")
        self.lbl_sqi.setText("SQI (Signál): ---%")
        self.lbl_status.setText("ZRUŠENO - PŘIPRAVENO")
        self.lbl_status.setStyleSheet(
            "color: #AAAAAA; font-size: 16px; font-weight: bold; letter-spacing: 2px;")

    def clear_positions(self):
        for k in self.pos_data:
            self.pos_data[k] = None
            self.pos_labels[k].setText("NEZAZNAMENÁNO")
            self.pos_labels[k].setStyleSheet("font-size: 14px; color: #666666; font-weight: bold;")

    # ─────────────────────────── AUDIO CALLBACK ──────────────────────────

    def audio_callback(self, indata, frames, time_info, status):
        self.current_time_sec += frames / self.sample_rate

        raw = indata[:, 0]
        if self.sos is not None:
            filtered, self.zi = signal.sosfilt(self.sos, raw, zi=self.zi)
        else:
            filtered = raw

        processed = np.clip(filtered * self.settings['gain'], -1.0, 1.0)

        # Sekundární amplitude filtr (1000-8000 Hz, bez gain clipping)
        sos_amp = self.amplitude_estimator._sos_amp
        if sos_amp is not None:
            amp_filtered, self.amplitude_estimator._zi_amp = signal.sosfilt(
                sos_amp, raw, zi=self.amplitude_estimator._zi_amp)
        else:
            amp_filtered = raw

        self.audio_data = np.roll(self.audio_data, -frames)
        self.audio_data[-frames:] = processed

        # Udržujeme i amplitude buffer (bez gain, bez clipu)
        if not hasattr(self, '_amp_audio_data'):
            self._amp_audio_data = np.zeros(self.sample_rate * 2)
        self._amp_audio_data = np.roll(self._amp_audio_data, -frames)
        self._amp_audio_data[-frames:] = amp_filtered

        if not self.is_playing:
            return
        
        # ── 1. KONTINUÁLNÍ AUTO-THRESHOLD (Běží neustále) ────────────────
        if not self.settings.get('manual_threshold', False):
            # Používáme 98. percentil z framu - ignoruje ojedinělé extrémní špičky šumu
            frame_peak = np.percentile(np.abs(processed), 98)
            if frame_peak > 0.005:  # Ignorujeme absolutní ticho
                self._thresh_history.append(frame_peak)
                
                # Zvětšený buffer (50) pro stabilitu
                if len(self._thresh_history) >= 30:
                    sorted_peaks = np.sort(list(self._thresh_history))
                    # Výpočet dynamického šumu a signálu
                    noise_floor = np.median(sorted_peaks[:10])
                    signal_top = np.median(sorted_peaks[-10:])
                    
                    # Cílový práh je 35 % nad úrovní šumu směrem k signálu
                    target_thresh = noise_floor + (signal_top - noise_floor) * 0.35
                    target_thresh = np.clip(target_thresh, 0.015, 0.85)
                    
                    # EMA stabilizace (zabraňuje skokům na displeji)
                    alpha = 0.03
                    self.settings['threshold'] = (self.settings['threshold'] * (1 - alpha)) + (target_thresh * alpha)

        # ── 2. SETTLING FÁZE (Pouze blokuje vyhodnocení, nezastavuje práh) ──
        elapsed = self.current_time_sec - self.start_time_sec
        if elapsed < self.settings['settling_time']:
            self.first_tick_time = None
            return

        # ── 3. TICK DETECTION (Původní logika pokračuje zde...) ──────────
        beat_int = 3600.0 / self.active_bph
        # ...

        # ── Settling fáze ────────────────────────────────────────────────
        elapsed = self.current_time_sec - self.start_time_sec
        if elapsed < self.settings['settling_time']:
            self.first_tick_time = None
            if not self.settings.get('manual_threshold', False):
                peak = np.max(np.abs(processed))
                if peak > 0.02:
                    self._thresh_history.append(peak)
                    if len(self._thresh_history) >= 5:
                        # Adaptivní práh: 40. percentil z historických peaků
                        target = float(np.percentile(list(self._thresh_history), 40)) * 0.55
                        target = max(0.010, min(target, 0.80))
                        alpha  = 0.05  # pomalé sledování
                        if self.settings['threshold'] < 0.01:
                            self.settings['threshold'] = target
                        else:
                            self.settings['threshold'] = (
                                self.settings['threshold'] * (1 - alpha) + target * alpha)
            return

        # ── Tick detection ────────────────────────────────────────────────
        beat_int = 3600.0 / self.active_bph

        if np.max(np.abs(processed)) <= self.settings['threshold']:
            self.cooldown = max(0, self.cooldown - frames)
            return

        for i in range(frames):
            if self.cooldown > 0:
                self.cooldown -= 1
                continue

            if abs(processed[i]) > self.settings['threshold']:
                # Přesný čas tiku
                tick_t = (self.current_time_sec
                          - (frames / self.sample_rate)
                          + (i / self.sample_rate))

                # ── Extrakce audio okna pro výpočet amplitudy ────────────
                # Okno: 5ms pre-trigger + 35ms post (pokryje celý tick burst)
                # Používáme AMPLITUDE BUFFER (filtr 1000-8000Hz, bez gain)
                pre_samp  = int(self.sample_rate * 0.005)
                post_samp = int(self.sample_rate * 0.035)

                idx_center = len(self._amp_audio_data) - frames + i
                idx_start  = max(0, idx_center - pre_samp)
                idx_end    = min(len(self._amp_audio_data), idx_center + post_samp)
                audio_window = self._amp_audio_data[idx_start:idx_end]

                # Výpočet amplitudy – Block-Energy Group metoda
                # is_even bude určeno v process_tick (zatím None, doplníme po registraci)
                # Předáme okno do processtick který zná is_even
                self._pending_amp_window = audio_window

                self.process_tick(tick_t, self._pending_amp_window)

                # Cooldown: 60% beat intervalu (zabraňuje double-trigger)
                self.cooldown = int(self.sample_rate * beat_int * 0.60)
                break  # jeden tik na jeden callback frame

    # ─────────────────────────── TICK PROCESSING ─────────────────────────

    def process_tick(self, t: float, amp_window: np.ndarray | None):
        beat_int = 3600.0 / self.active_bph

        if self.first_tick_time is None:
            self.first_tick_time = t
            self.last_tick_time  = t
            self.beat_counter    = 0
            self.lbl_status.setText("MĚŘENÍ PROBÍHÁ")
            self.lbl_status.setStyleSheet(
                "color: #00FF66; font-size: 16px; font-weight: bold; letter-spacing: 2px;")
            return

        dt = t - self.last_tick_time

        # ── AUTO BPH detekce ─────────────────────────────────────────────
        if self.settings['bph'] == 'AUTO':
            n_ticks = len(self.rate_estimator._even) + len(self.rate_estimator._odd)
            if n_ticks < 6:
                rates = {14400: 0.25, 18000: 0.2, 21600: 1/6, 28800: 0.125, 36000: 0.1}
                best  = min(rates, key=lambda k: abs(rates[k] - dt))
                if abs(rates[best] - dt) < 0.045:
                    self.active_bph = best
                    beat_int = 3600.0 / self.active_bph

        # ── Počet kroků (kompenzace vynechaných tiků) ────────────────────
        steps = round(dt / beat_int)
        if steps < 1:
            return

        if steps > 1:
            self.signal_quality = max(0.0, self.signal_quality - 4.0 * steps)
        elif abs(dt - beat_int) > beat_int * 0.08:
            self.signal_quality = max(0.0, self.signal_quality - 1.5)
        else:
            self.signal_quality = min(100.0, self.signal_quality + 0.3)

        self.last_tick_time  = t
        self.beat_counter   += steps
        is_even = (self.beat_counter % 2 == 0)

        # ── Rate estimátor ───────────────────────────────────────────────
        self.rate_estimator.add_interval(dt, is_even, beat_int)
        rate_val, be_val = self.rate_estimator.compute(beat_int)
        if rate_val is not None:
            self.current_rate = rate_val
            self.current_be   = be_val

        # ── Amplituda – Block-Energy Group metoda ────────────────────────
        # Teď víme is_even, takže můžeme správně přidat do kanálu
        if amp_window is not None and len(amp_window) > 10:
            amp_val = self.amplitude_estimator.add_measurement(
                amp_window,
                self.settings['lift_angle'],
                self.active_bph,
                is_even
            )
        else:
            amp_val = None

        if amp_val is not None:
            self.current_amp = amp_val

        # ── Graf (fázový posun – papírový váleček) ───────────────────────
        expected_t = self.first_tick_time + (self.beat_counter * beat_int)
        dev_ms     = (expected_t - t) * 1000.0   # + = rychlé (stoupá nahoru)

        max_ticks = int(self.settings['averaging_period'] * self.active_bph / 3600.0)
        self.raw_deviations.append(dev_ms)
        if len(self.raw_deviations) > max_ticks:
            self.raw_deviations.pop(0)

        plot_limit = int(self.active_bph / 3600.0 * 60)
        self.plot_data.append((t, dev_ms, is_even))
        if len(self.plot_data) > plot_limit:
            self.plot_data.pop(0)

    # ─────────────────────────── GUI UPDATE ──────────────────────────────

    def update_gui(self):
        # Osciloskop
        if self.stack.currentIndex() == 1:
            time_axis = np.linspace(0, 2.0, len(self.audio_data))
            self.audio_curve.setData(x=time_axis, y=self.audio_data)
            self.thresh_line.setValue(self.settings['threshold'])
            self.thresh_line_neg.setValue(-self.settings['threshold'])
            mode_text = "[MANUÁL]" if self.settings.get('manual_threshold') else "[AUTO]"
            self.lbl_scope_thresh.setText(
                f"PRÁH {mode_text}: {self.settings['threshold']:.3f}")

        if not self.is_playing:
            return

        # Settling countdown
        elapsed = self.current_time_sec - self.start_time_sec
        if elapsed < self.settings['settling_time']:
            rem = int(self.settings['settling_time'] - elapsed)
            self.lbl_status.setText(f"STABILIZACE... {rem}s")
            self.lbl_status.setStyleSheet(
                "color: #00E5FF; font-size: 16px; font-weight: bold; letter-spacing: 2px;")
            return

        # ── Timegrapher plot ─────────────────────────────────────────────
        if self.stack.currentIndex() == 0 and self.plot_data and self.first_tick_time:
            t0         = self.first_tick_time
            sweep_pos  = (self.current_time_sec - t0) % 60.0
            self.sweep_line.setPos(sweep_pos)

            even_x, even_y, odd_x, odd_y = [], [], [], []
            for pt_t, pt_dev, is_even in self.plot_data:
                x = (pt_t - t0) % 60.0
                y = ((pt_dev + 40.0) % 80.0) - 40.0
                if is_even:
                    even_x.append(x); even_y.append(y)
                else:
                    odd_x.append(x); odd_y.append(y)

            self.scatter_even.setData(x=even_x, y=even_y)
            self.scatter_odd.setData(x=odd_x, y=odd_y)

        # ── Displeje ─────────────────────────────────────────────────────
        tc = self.rate_estimator.sample_count()
        # Minimální počet vzorků shodný s RateEstimator.MIN_PAIRS
        min_display = RateEstimator.MIN_PAIRS
        if tc < min_display and tc > 0:
            # Warm-up fáze – zobrazíme progress ale ne hodnotu
            needed = min_display
            self.disp_rate.info_label.setText(f"Warm-up: {tc}/{needed} tiků...")
            self.disp_amp.info_label.setText(f"Sbírám data ({tc} tiků)...")
            self.disp_be.info_label.setText(f"Sbírám data...")
            self.lbl_grade.setText(f"WARM-UP  {tc}/{needed}")
            self.lbl_grade.setStyleSheet(
                "color: #888888; font-size: 20px; font-weight: bold; letter-spacing: 1px;")
        if tc >= min_display:
            std = self.settings.get('tolerance_std', 'COSC (-4/+6 s/d)')
            is_good = False
            if "COSC" in std:
                is_good = (-4 <= self.current_rate <= 6
                           and self.current_amp > 250
                           and self.current_be < 0.6)
            elif "Vintage" in std:
                is_good = (-15 <= self.current_rate <= 15
                           and self.current_amp > 200
                           and self.current_be < 1.5)
            else:
                is_good = (-10 <= self.current_rate <= 10
                           and self.current_amp > 220
                           and self.current_be < 1.0)

            if is_good:
                self.lbl_grade.setText(f"HODNOCENÍ: VYHOVUJE ({std})")
                self.lbl_grade.setStyleSheet(
                    "color: #00FF66; font-size: 20px; font-weight: bold; letter-spacing: 1px;")
            else:
                self.lbl_grade.setText("HODNOCENÍ: NUTNÝ SERVIS / SEŘÍZENÍ")
                self.lbl_grade.setStyleSheet(
                    "color: #FF3366; font-size: 20px; font-weight: bold; letter-spacing: 1px;")

            c_sqi = ("#00FF66" if self.signal_quality > 85
                     else "#FFB300" if self.signal_quality > 60
                     else "#FF3366")
            self.lbl_sqi.setText(f"SQI (Signál): {int(self.signal_quality)}%")
            self.lbl_sqi.setStyleSheet(
                f"color: {c_sqi}; font-size: 16px; font-weight: bold;")

            c_rate = "#00E5FF" if abs(self.current_rate) <= 15 else "#FF3366"
            self.disp_rate.value_label.setText(f"{self.current_rate:+.1f}")
            self.disp_rate.value_label.setStyleSheet(
                f"color: {c_rate}; font-size: 55px; font-weight: bold; font-family: Consolas;")
            self.disp_rate.info_label.setText(f"Zprůměrováno z {tc} bodů")

            c_amp = ("#00E5FF" if 250 <= self.current_amp <= 320
                     else "#FFB300" if 200 <= self.current_amp < 250
                     else "#FF3366")
            self.disp_amp.value_label.setText(f"{int(self.current_amp)}°")
            self.disp_amp.value_label.setStyleSheet(
                f"color: {c_amp}; font-size: 55px; font-weight: bold; font-family: Consolas;")
            self.disp_amp.info_label.setText(
                f"LA={self.settings['lift_angle']}° | {self.active_bph} BPH | T13-metoda")

            c_beat = ("#00E5FF" if self.current_be <= 0.5
                      else "#FFB300" if self.current_be <= 1.0
                      else "#FF3366")
            self.disp_be.value_label.setText(f"{self.current_be:.1f} ms")
            self.disp_be.value_label.setStyleSheet(
                f"color: {c_beat}; font-size: 55px; font-weight: bold; font-family: Consolas;")
            self.disp_be.info_label.setText(f"BPH: {self.active_bph}")

    # ─────────────────────────── POSITION SAVE ───────────────────────────

    def save_position(self, pos_name):
        if self.rate_estimator.sample_count() < 10:
            QtWidgets.QMessageBox.warning(
                self, "Nedostatek dat",
                "Pro uložení polohy nechte měření běžet déle.")
            return

        self.pos_data[pos_name] = {
            'rate': self.current_rate,
            'amp':  self.current_amp,
            'be':   self.current_be
        }

        lbl = self.pos_labels[pos_name]
        lbl.setText(
            f"{self.current_rate:+.1f} s/d  |  {int(self.current_amp)}°  |  {self.current_be:.1f} ms")
        lbl.setStyleSheet("font-size: 16px; color: #00E5FF; font-weight: bold;")

    # ─────────────────────────── ANALYSIS TAB ────────────────────────────

    def update_analysis_tab(self):
        all_ints = list(self.rate_estimator._even) + list(self.rate_estimator._odd)
        if len(all_ints) < 10:
            self.lbl_ana_drift.setText("Trend Grafu: Čekám na data")
            self.lbl_ana_var.setText("Stabilita (Rozptyl): Čekám na data")
            self.lbl_ana_sqi.setText("Kvalita Signálu (SQI): Čekám na data")
            self.lbl_action_plan.setText("PRO DETAILNÍ ANALÝZU ZMĚŘTE ALESPOŇ 10 TIKŮ...")
            self.lbl_action_plan.setStyleSheet("color: #888888;")
            return

        std_dev = np.std(all_ints) * 1000.0

        drift = "Stabilní"
        if len(all_ints) > 50:
            h1 = np.mean(all_ints[:25])
            h2 = np.mean(all_ints[-25:])
            if abs(h2) > abs(h1) + 0.0002:
                drift = "Zhoršuje se (Drift od středu)"
            elif abs(h2) < abs(h1) - 0.0002:
                drift = "Zlepšuje se (Ustálení)"

        self.lbl_ana_drift.setText(f"Trend Grafu: {drift}")
        self.lbl_ana_var.setText(f"Stabilita (Rozptyl): {std_dev:.2f} ms")
        self.lbl_ana_sqi.setText(f"Kvalita Signálu (SQI): {int(self.signal_quality)}%")

        issues_found = False

        if std_dev > 1.5:
            self.lbl_err_esc.setText("• Detekován nepravidelný krok. Tření na paletách nebo vychozené čepy.")
            self.lbl_err_esc.setStyleSheet("color: #FF3366;")
            issues_found = True
        else:
            self.lbl_err_esc.setText("• Escapement: Krok je čistý a pravidelný.")
            self.lbl_err_esc.setStyleSheet("color: #00FF66;")

        if self.current_amp < 220:
            self.lbl_err_amp.setText("• Kriticky nízká amplituda (ztráta energie).")
            self.lbl_err_amp.setStyleSheet("color: #FF3366;")
            issues_found = True
        else:
            self.lbl_err_amp.setText("• Amplituda: Přenos energie je ideální.")
            self.lbl_err_amp.setStyleSheet("color: #00FF66;")

        if self.current_be > 0.8:
            self.lbl_err_be.setText("• Závažný Beat Error. Strojek silně 'kulhá'.")
            self.lbl_err_be.setStyleSheet("color: #FF3366;")
            issues_found = True
        else:
            self.lbl_err_be.setText("• Beat Error: Zámek v toleranci.")
            self.lbl_err_be.setStyleSheet("color: #00FF66;")

        if self.signal_quality < 80:
            self.lbl_err_noise.setText("• Silný hluk na pozadí. Nečistoty nebo uvolněné komponenty.")
            self.lbl_err_noise.setStyleSheet("color: #FFB300;")
            issues_found = True
        else:
            self.lbl_err_noise.setText("• Mechanický šum: Chod je tichý.")
            self.lbl_err_noise.setStyleSheet("color: #00FF66;")

        rates = [d['rate'] for d in self.pos_data.values() if d is not None]
        if len(rates) >= 3:
            delta = max(rates) - min(rates)
            self.lbl_ana_delta.setText(f"Delta (Rozdíl poloh): {delta:.1f} s/d")

            vert_keys = ["CROWN RIGHT (3H)", "CROWN LEFT (9H)", "CROWN UP (12H)", "CROWN DOWN (6H)"]
            valid_verts = {k: self.pos_data[k]['rate']
                          for k in vert_keys if self.pos_data[k] is not None}
            if len(valid_verts) >= 3:
                slowest_pos = min(valid_verts, key=valid_verts.get)
                max_v = max(valid_verts.values())
                min_v = min(valid_verts.values())
                if (max_v - min_v) > 10:
                    self.lbl_ana_heavy.setText(
                        f"Poise Error: Těžký bod na věnci směrem dolů v pozici {slowest_pos}.")
                    self.lbl_ana_heavy.setStyleSheet("color: #FFB300;")
                else:
                    self.lbl_ana_heavy.setText(
                        "Vyvážení: Setrvačka je perfektně vyvážená (Zero Poise Error).")
                    self.lbl_ana_heavy.setStyleSheet("color: #00FF66;")
        else:
            self.lbl_ana_delta.setText("Delta: Změřte alespoň 3 polohy.")
            self.lbl_ana_heavy.setText("Vyvážení: Změřte vertikální polohy.")
            self.lbl_ana_heavy.setStyleSheet("color: #888888;")

        action_plan = ""
        if self.current_be > 0.8:
            action_plan += ("1. BEAT ERROR KOREKCE: Posuňte špalíček vlásku (stud carrier). "
                           "U vintage strojků (pevný špalek) je nutné sejmout setrvačku a opatrně "
                           "pootočit věncem na hřídeli vůči vlásku.\n")

        if len(rates) >= 3 and (max(rates) - min(rates)) > 15:
            action_plan += ("2. POISE ERROR (Vyvážení): Detekován těžký bod. Statické vyvážení - "
                           "odeberte materiál (vrtáním/frézováním) v detekovaném bodě, nebo přidejte "
                           "zátěž na protilehlý vyvažovací šroubek.\n")

        if std_dev > 1.5:
            action_plan += ("3. SERVIS KROKU: Extrémní variance. Vyjměte a mikroskopicky zkontrolujte "
                           "opotřebení krokového kola a palet. Proveďte chemické čištění a aplikujte "
                           "exaktní množství maziva Moebius (Epilame povrchová úprava doporučena).\n")

        if self.current_amp < 220:
            action_plan += ("4. PŘENOS ENERGIE: Amplituda je mrtvá. Zkontrolujte axiální vůle soukolí. "
                           "Pokud je uložení čisté, hnací pero (mainspring) je unavené a vyžaduje "
                           "okamžitou výměnu za nové.\n")

        if not issues_found and abs(self.current_rate) > 6:
            action_plan += ("1. REGULACE: Mechanika běží výborně. Jemně korigujte regulační ručku "
                           "mikroregulace pro stažení denní odchylky blíž k nule.\n")

        if not action_plan:
            action_plan = "Strojek vykazuje optimální laboratorní hodnoty a nevyžaduje zásah."

        self.lbl_action_plan.setText(action_plan)
        self.lbl_action_plan.setStyleSheet(
            "font-size: 15px; font-weight: normal; color: #FFFFFF; line-height: 1.5;")


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = TimegrapherApp()
    window.show()
    sys.exit(app.exec_())