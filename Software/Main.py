import sys
import numpy as np
import sounddevice as sd
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

# Vzorkovací frekvence zvuku
SAMPLE_RATE = 44100      

class TimegrapherApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Watch Timegrapher - Interaktivní Prototyp")
        self.resize(1200, 800)

        # --- ZÁKLADNÍ PROMĚNNÉ ---
        self.bph = 21600
        self.bps = self.bph / 3600.0
        self.beat_interval = 1.0 / self.bps
        self.threshold = 0.2
        
        self.audio_data = np.zeros(SAMPLE_RATE * 2) # Zobrazujeme poslední 2 sekundy zvuku
        self.tick_times = []      
        self.deviations = []      
        self.first_tick_time = None
        self.current_time_sec = 0.0
        
        self.cooldown = 0
        self.cooldown_samples = int(SAMPLE_RATE * (self.beat_interval * 0.6))
        
        self.is_playing = True # Stav pro spuštění/pozastavení

        # --- GUI ROZVRŽENÍ ---
        main_widget = QtWidgets.QWidget()
        self.setCentralWidget(main_widget)
        layout = QtWidgets.QVBoxLayout(main_widget)

        # HORNÍ OVLÁDACÍ PANEL
        control_layout = QtWidgets.QHBoxLayout()
        
        # 1. Výběr BPH
        self.bph_label = QtWidgets.QLabel("Frekvence (BPH):")
        self.bph_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.bph_combo = QtWidgets.QComboBox()
        self.bph_combo.addItems(["14400", "18000", "21600", "28800", "36000"])
        self.bph_combo.setCurrentText("21600")
        self.bph_combo.currentTextChanged.connect(self.change_bph)
        
        # 2. Textový ukazatel aktuálního prahu
        self.thresh_label = QtWidgets.QLabel(f"Aktuální práh (Threshold): {self.threshold:.3f}")
        self.thresh_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #b8860b;")
        
        # 3. Tlačítko Play/Stop
        self.btn_play = QtWidgets.QPushButton("Pozastavit")
        self.btn_play.setStyleSheet("background-color: #ffcccc; font-weight: bold;")
        self.btn_play.clicked.connect(self.toggle_play)

        # 4. Tlačítko pro vymazání starých dat z grafu
        self.btn_clear = QtWidgets.QPushButton("Vymazat graf")
        self.btn_clear.clicked.connect(self.clear_graph)

        control_layout.addWidget(self.bph_label)
        control_layout.addWidget(self.bph_combo)
        control_layout.addStretch()
        control_layout.addWidget(self.thresh_label)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_play)
        control_layout.addWidget(self.btn_clear)
        
        layout.addLayout(control_layout)

        # GRAF 1: Surový zvukový signál + Interaktivní čára
        self.plot_audio = pg.PlotWidget(title="1. Načítání signálu (Táhni za žlutou čáru pro nastavení prahu detekce)")
        self.plot_audio.setYRange(-1, 1)
        self.plot_audio.showGrid(x=True, y=True)
        self.audio_curve = self.plot_audio.plot(pen='c') # Azurová barva signálu
        
        # Posuvná čára pro Threshold (Kladná)
        self.thresh_line = pg.InfiniteLine(angle=0, movable=True, pos=self.threshold, pen=pg.mkPen('y', width=3))
        self.thresh_line.setBounds([-1, 1]) # Omezení, aby s ní nešlo ujet mimo graf
        self.thresh_line.sigPositionChanged.connect(self.update_threshold)
        self.plot_audio.addItem(self.thresh_line)
        
        # Zrcadlová čára pro záporné špičky (Automaticky se hýbe podle té horní)
        self.thresh_line_neg = pg.InfiniteLine(angle=0, movable=False, pos=-self.threshold, pen=pg.mkPen('y', width=2, style=QtCore.Qt.DashLine))
        self.plot_audio.addItem(self.thresh_line_neg)

        layout.addWidget(self.plot_audio)

        # GRAF 2: Timegrapher (Watch-O-Scope styl)
        self.plot_dots = pg.PlotWidget(title="2. Zobrazení tiků (Čas vs. Odchylka)")
        self.plot_dots.setLabel('left', 'Odchylka (ms)')
        self.plot_dots.setLabel('bottom', 'Čas (s)')
        self.plot_dots.showGrid(x=True, y=True)
        self.scatter = pg.ScatterPlotItem(size=6, pen=pg.mkPen(None), brush=pg.mkBrush(255, 50, 50, 255))
        self.plot_dots.addItem(self.scatter)
        layout.addWidget(self.plot_dots)

        # --- AUDIO STREAM A ČASOVAČ ---
        self.stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, callback=self.audio_callback)
        self.stream.start()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(50)

    # --- FUNKCE PRO ZPRACOVÁNÍ GUI AKCÍ ---

    def toggle_play(self):
        """Přepíná stav mezi spuštěno a pozastaveno"""
        self.is_playing = not self.is_playing
        if self.is_playing:
            self.btn_play.setText("Pozastavit")
            self.btn_play.setStyleSheet("background-color: #ffcccc; font-weight: bold;")
        else:
            self.btn_play.setText("Spustit")
            self.btn_play.setStyleSheet("background-color: #ccffcc; font-weight: bold;")

    def update_threshold(self):
        """Volá se pokaždé, když uživatel pohne žlutou čárou v grafu"""
        val = self.thresh_line.value()
        self.threshold = abs(val) # Práh bereme vždy jako kladné číslo
        
        # Srovnáme čáry do zrcadla, pokud by ji uživatel stáhl do mínusu
        self.thresh_line.setValue(self.threshold) 
        self.thresh_line_neg.setValue(-self.threshold)
        
        # Aktualizujeme textový label
        self.thresh_label.setText(f"Aktuální práh (Threshold): {self.threshold:.3f}")

    def change_bph(self, text):
        """Volá se při změně BPH z rozbalovacího menu"""
        self.bph = int(text)
        self.bps = self.bph / 3600.0
        self.beat_interval = 1.0 / self.bps
        # Přepočítáme ochranný interval (cooldown) pro novou frekvenci
        self.cooldown_samples = int(SAMPLE_RATE * (self.beat_interval * 0.6))
        self.clear_graph() # Vyčistíme graf pro nové měření

    def clear_graph(self):
        """Vymaže historii tiků z grafu"""
        self.tick_times = []
        self.deviations = []
        self.first_tick_time = None
        self.current_time_sec = 0.0
        self.scatter.clear()

    # --- FUNKCE PRO ZPRACOVÁNÍ ZVUKU ---

    def audio_callback(self, indata, frames, time_info, status):
        """Zpracovává zvuk ze zvukové karty vzorek po vzorku"""
        if status:
            pass # Skryjeme varovné hlášky, aby to nespamovalo konzoli
            
        # I když je pauza, musíme nechat běžet čas, jinak by nám vznikla mezera po znovuspuštění
        if not self.is_playing:
            self.current_time_sec += frames / SAMPLE_RATE
            return
        
        audio_chunk = indata[:, 0]
        
        # Posuneme starý zvuk do strany a vložíme nový (pro vykreslení)
        self.audio_data = np.roll(self.audio_data, -frames)
        self.audio_data[-frames:] = audio_chunk

        # Detekce tiků s využitím uživatelem nastaveného prahu (self.threshold)
        for i in range(frames):
            if self.cooldown > 0:
                self.cooldown -= 1
                continue
            
            # Jakmile špička překročí nastavenou žlutou čáru
            if abs(audio_chunk[i]) > self.threshold:
                tick_time = self.current_time_sec + (i / SAMPLE_RATE)
                self.process_tick(tick_time)
                self.cooldown = self.cooldown_samples
        
        self.current_time_sec += frames / SAMPLE_RATE

    def process_tick(self, t):
        """Vypočítá odchylku tiku a přidá ho do spodního grafu"""
        if self.first_tick_time is None:
            self.first_tick_time = t
            return

        dt = t - self.first_tick_time
        N = round(dt * self.bps)
        expected_time = N * self.beat_interval
        
        deviation_sec = expected_time - dt 
        deviation_ms = deviation_sec * 1000.0

        self.tick_times.append(t)
        self.deviations.append(deviation_ms)

        # Udržujeme jen posledních 600 teček v paměti (cca 100 sekund pro 6 BPS)
        if len(self.tick_times) > 600:
            self.tick_times.pop(0)
            self.deviations.pop(0)

    def update_gui(self):
        """Vykresluje data na obrazovku 20x za sekundu"""
        if not self.is_playing:
            return
            
        self.audio_curve.setData(self.audio_data[::10]) # Každý 10. bod z audia pro plynulost
        
        if len(self.tick_times) > 0:
            self.scatter.setData(x=self.tick_times, y=self.deviations)
            
            # FIXOVÁNÍ OSY X - Zobrazení oken o velikosti 15 sekund
            window_size = 15.0
            t_first = self.tick_times[0]
            t_latest = self.tick_times[-1]
            
            # Dokud od prvního tiku neuběhlo 15 sekund, osa začíná u nuly a jde dopředu
            if (t_latest - t_first) < window_size:
                self.plot_dots.setXRange(t_first, t_first + window_size, padding=0.01)
            # Jakmile dosáhneme 15 sekund, osa se začne plynule posouvat doprava s novými tiky
            else:
                self.plot_dots.setXRange(t_latest - window_size, t_latest, padding=0.01)

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = TimegrapherApp()
    window.show()
    sys.exit(app.exec_())