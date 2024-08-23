import numpy as np
import sounddevice as sd
import tkinter as tk
from openai import OpenAI
import threading
import queue
import pyaudio
import wave

rate = 16000  # 采样率/Hz
channels = 2
buffer_size = 140960

class AudioCapture:
    def __init__(self, device_index=None):
        self.audio_queue = queue.Queue()
        self.is_recording = True
        self.device_index = device_index  # 设备索引

        # 初始化PyAudio
        self.pyaudio_instance = pyaudio.PyAudio()

    def start(self):
        # 打开音频流
        self.stream = self.pyaudio_instance.open(format=pyaudio.paInt16,
                                                  channels=channels,  # 使用立体声
                                                  rate=rate,
                                                  input=True,
                                                  input_device_index=self.device_index,
                                                  frames_per_buffer=buffer_size,
                                                  stream_callback=self.audio_callback)
        self.stream.start_stream()
        print("音频捕获开始...")

    def audio_callback(self, in_data, frame_count, time_info, status):
        if status:
            print(status)
        self.audio_queue.put(np.frombuffer(in_data, dtype=np.int16))  # 将音频数据放入队列
        return (None, pyaudio.paContinue)

    def stop(self):
        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_instance.terminate()
        print("音频捕获停止。")

    def get_audio_data(self):
        while not self.audio_queue.empty():
            yield self.audio_queue.get()


class AudioTranscriber:
    def __init__(self, model_name="Systran/faster-distil-whisper-large-v3", api_key="", api_url="http://home.dogegg.online:8000/v1/"):
        self.model_name = model_name
        self.api_key = api_key
        self.api_url = api_url
        self.openai = OpenAI(api_key=self.api_key, base_url=self.api_url)

    def transcribe_audio(self, audio_data):
        # 保存音频数据为临时文件
        with wave.open("tmp.wav", "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(pyaudio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(rate)
            wf.writeframes(audio_data)
        try:
            # 读取音频文件并进行转录
            with open("tmp.wav", "rb") as audio_file:
                response = self.openai.audio.transcriptions.create(
                    model=self.model_name,
                    file=audio_file
                )
            print(response.text)
            return response.text
        except Exception as e:
            print(f"转录音频时发生错误: {e}")
            return "获取字幕失败"
        
class SubtitleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("实时字幕")
        self.text_area = tk.Text(root, wrap=tk.WORD)
        self.text_area.pack(expand=True, fill=tk.BOTH)
        self.transcriber = AudioTranscriber()
        self.audio_capture = AudioCapture(device_index=1)  # 使用虚拟音频设备索引
        self.is_running = True

        self.start_transcription()

    def start_transcription(self):
        self.audio_capture.start()
        threading.Thread(target=self.process_audio).start()

    def process_audio(self):
        while self.is_running:
            if not self.audio_capture.audio_queue.empty():
                audio_data = self.audio_capture.audio_queue.get()
                print(f"捕获音频数据长度: {len(audio_data)}")
                transcription = self.transcriber.transcribe_audio(audio_data)
                self.update_subtitle(transcription)

    def update_subtitle(self, text):
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)

    def stop(self):
        self.is_running = False
        self.audio_capture.stop()


def main():
    print(sd.query_devices())
    root = tk.Tk()
    app = SubtitleApp(root)

    def on_closing():
        app.stop()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

    # p = pyaudio.PyAudio()

    # for i in range(p.get_device_count()):
    #     info = p.get_device_info_by_index(i)
    #     print(f"设备 {i}: {info['name']} - 最大输入通道: {info['maxInputChannels']}, 最大输出通道: {info['maxOutputChannels']}, 支持的采样率: {info['defaultSampleRate']}")

if __name__ == "__main__":
    main()
