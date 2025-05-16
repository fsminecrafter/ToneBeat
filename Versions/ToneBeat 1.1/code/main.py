import PyQt5 as Pq5
from pathlib import Path
import os
import sys
import subprocess
import threading
import time
import numpy as np
import sounddevice as sd
import scipy.io.wavfile as wavfile
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QDialog, QApplication, QWidget, QMainWindow, QSlider, QDial, QLabel, QAction, QFileDialog, QMessageBox

ScriptDir = os.getcwd()
ScriptPath = Path(ScriptDir)
Tonebeat = ScriptPath.parent.absolute()
TonebeatUiName = "tonebeat.ui"
TonebeatUi = str(Tonebeat) + "/assets/" + TonebeatUiName
script = ScriptDir + "/main.py"
Speed = 0
Frequency = 400

print("Tonebeat is here at:", ScriptDir)
print("Parent: ", Tonebeat)
print("TonebeatUi", TonebeatUi)

class Dialog(QDialog):
    def __init__(self):
        super(Dialog, self).__init__()
        loadUi(TonebeatUi, self)
        self.bpm = Speed
        self.Frequency = Frequency
        self.Sound = "Beep"
        self.New.clicked.connect(self.newwindow)
        self.Speed.valueChanged.connect(self.UpdateSpeed)
        self.Freq.valueChanged.connect(self.UpdateFrequency)
        self.SoundSelect.addItems(["Beep (Defualt)", "Add new sound..."])
        self.SoundSelect.currentIndexChanged.connect(self.comboboxChange)
        
        self.sounds = {}
        
        self.thread = None
        
        self.thread = beeper(Speed, Frequency, self)
        self.thread.start()
        
    def comboboxChange(self):
        if self.SoundSelect.currentText() == "Add new sound...":
            self.OpenSoundFile()
            
    def OpenSoundFile(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select WAV", "", "WAV Files (*.wav)")
        if not path:
            self.SoundSelect.setCurrentIndex(0)
            return
        
        try:
            samplerate, data = wavfile.read(path)
            if len(data.shape) > 1:
                data = data[:, 0]
            duration = len(data) / samplerate
            if duration > 1.0:
                raise ValueError("Audio is longer than 1 second")
            
            name = os.path.basename(path)
            if name not in self.sounds:
                self.SoundSelect.insertItem(self.SoundSelect.count() - 1, name)
                self.sounds[name] = (samplerate, data)
            self.SoundSelect.setCurrentText(name)
            
        except Exception as e:
            QMessageBox.critical(self, "Invalid Sound", f"Failed to load sound:\n{e}")
            self.SoundSelect.setCurrentIndex(0)
            import traceback
            print("Unhandled exception: ", e)
            traceback.print_exc()
    
    def stop_thread(self):
        if self.thread and self.thread.is_alive():
            self.thread.stop()
            self.thread.stop()
            self.thread.join()
            print("Stopping thread...")
        
    def closeEvent(self, event):
        print("Exiting...")
        self.stop_thread()
        event.accept()
        
    def updateThread_parameters(self):
        if self.thread and self.thread.is_alive():
            self.thread.update_parameters(self.bpm, self.Frequency)
            print(f"Sending update {self.bpm} bpm, {self.Frequency} Hz")
    
    def newwindow(self):
        python_executable = sys.executable
        subprocess.Popen([python_executable, script])
        
    def UpdateSpeed(self, value):
        speed = value
        self.bpm = value
        self.CurrentSpeed.setText(str(value))
        self.updateThread_parameters()
        
    def UpdateFrequency(self, value):
        frequency = value
        self.Frequency = value
        self.CurrentFrequency.setText(str(value))
        self.updateThread_parameters()
    

class beeper(threading.Thread):
    def __init__(self, speed, freq, parentWindow):
        super().__init__()
        self.window = parentWindow
        self._lock = threading.Lock()
        self.running = True
        self.speed = speed
        self.freq = freq
        self.StopFlag = False
    
    def interuptableSleep(self, duration, cycles=0.1):
        start = time.time()
        self.StopFlag = False
        while time.time() - start < duration:
            if self.StopFlag:
                print("Sleep interupted")
                return
            time.sleep(cycles)
    
    def PlaySound(self, freq):
        choice = self.window.SoundSelect.currentText()
        if choice == "Beep (Defualt)":
            self.beep(freq)
        elif choice in self.window.sounds:
            samplerate, data = self.window.sounds[choice]
            print(f"[Thread] Samplerate of sound: {str(samplerate)}")
            sd.play(data.astype(np.float32), samplerate=samplerate)
        else:
            QMessageBox.warning(self, "Playback Error", "No valid sounds selected.")
    
    def beep(self, freq, duration=100, volume=0.5):
        samplingRate = 44100
        duration_s = duration / 1000
        t = np.linspace(0, duration_s, int(samplingRate * duration_s), endpoint=False)
        waveform = volume * np.sin(2 * np.pi * freq * t)
        
        sd.play(waveform.astype(np.float32), samplerate=samplingRate)
        while sd.get_stream().active:
            if self.StopFlag:
                sd.stop()
                break
            time.sleep(0.1)
        sd.wait()
    
    def run(self):
        print("[Thread] Started")
        while self.running:
            with self._lock:
                speed = self.speed
                freq = self.freq
            if speed <= 0:
                print("[Thread] Speed is 0, sleeping...")
                time.sleep(0.1)
                continue
            else:
                interval = 60 / self.speed
                print(f"[Thread] Playing! at: {interval:.2f}s")
                self.PlaySound(self.freq)
                self.interuptableSleep(interval)
                
            print(f"[Thread] Tick at {freq} Hz (every {interval:.2f}s)")
        
    def update_parameters(self, speed, freq):
        with self._lock:
            self.speed = speed
            self.freq = freq
        self.StopFlag = True
        print(f"[Thread] Updated parameters: Speed: {speed} BPM, Frequency: {freq} Hz")

            
    def stop(self):
        self.running = False
        
        
app = QApplication(sys.argv)
main = Dialog()
main.setWindowTitle("ToneBeat")
main.show()  

try:
    window = app.exec_()
    sys.exit(window)
except Exception as e:
    import traceback
    print("Unhandled exception: ", e)
    traceback.print_exc()
