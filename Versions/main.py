import PyQt5 as Pq5
from pathlib import Path
import os
import sys
import subprocess
import threading
import time
import numpy as np
import sounddevice as sd
from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QDialog, QApplication, QWidget, QMainWindow, QSlider, QDial, QLabel, QAction

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
        self.New.clicked.connect(self.newwindow)
        self.Speed.valueChanged.connect(self.UpdateSpeed)
        self.Freq.valueChanged.connect(self.UpdateFrequency)
        
        self.thread = None
        
        self.thread = beeper(Speed, Frequency)
        self.thread.start()
    
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
    def __init__(self, speed, freq):
        super().__init__()
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
                print(f"[Thread] Beeping! at: {interval:.2f}s")
                self.beep(self.freq)
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
main.show()  

try:
    window = app.exec_()
    sys.exit(window)
except Exception as e:
    import traceback
    print("Unhandled exception: ", e)
    traceback.print_exc()