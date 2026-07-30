import numpy as np
import sounddevice as sd

class AudioSource:
    """マイク入力をFFTして u_bass / u_mid / u_high を供給する"""
    def __init__(self):
        self.bass = 0.0
        self.mid = 0.0
        self.high = 0.0
        self.stream = sd.InputStream(
            channels=1,
            samplerate=44100,
            blocksize=1024,
            callback=self.audio_callback,
        )
        self.stream.start()

    def audio_callback(self, indata, frames, time_info, status):

        samples = indata[:, 0]
        spectrum = np.abs(np.fft.rfft(samples))
        bass = spectrum[1:6].mean() 
        mid = spectrum[6:47].mean()      
        high = spectrum[47:200].mean()   
        
        self.bass = min(bass / 10.0, 1.0)
        self.mid = min(mid / 10.0, 1.0)
        self.high = min(high / 10.0, 1.0)
        

    def get_values(self):
        return {"u_bass": self.bass, "u_mid": self.mid, "u_high": self.high}
    
    
class TimeSource:
    def __init__(self, app):
        self.app = app

    def get_values(self):
        return {"u_time": self.app.my_time}
    
    