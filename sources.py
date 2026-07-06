import numpy as np
import sounddevice as sd

class AudioSource:
    """マイク入力をFFTして u_bass / u_mid / u_high を供給する"""
    def __init__(self):
        self.bass = 0.0
        self.mid = 0.0
        self.high = 0.0
        # マイクを開く。callbackが別スレッドで呼ばれ続ける
        self.stream = sd.InputStream(
            channels=1,
            samplerate=44100,
            blocksize=1024,
            callback=self.audio_callback,
        )
        self.stream.start()

    def audio_callback(self, indata, frames, time_info, status):
        # indata: 直近1024サンプルの音の波形(-1.0〜1.0)
        samples = indata[:, 0]
        # FFT: 波形→周波数成分(どの高さの音がどれだけ強いか)
        spectrum = np.abs(np.fft.rfft(samples))
        # 帯域で3分割して平均(индексは44100Hz/1024サンプル→1bin≈43Hz)
        bass = spectrum[1:6].mean()      # ~250Hz: キック、ベース
        mid = spectrum[6:47].mean()      # ~2kHz: ボーカル、シンセ
        high = spectrum[47:200].mean()   # ~8.6kHz: ハイハット、シズル
        # 雑に正規化(後でスライダー化する値。まず動かす用の決め打ち)
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
    
    