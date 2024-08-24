import numpy as np
import pyaudio
import tkinter as tk
import threading
import socket
import logging
import time

rate = 16000  # 采样率/Hz
channels = 1
max_chunk_size = 2048  # 每个音频块的最大大小（以帧为单位）

class AudioCapture:
    def __init__(self, device_index=None, server_host='192.168.1.2', server_port=43001):
        self.device_index = device_index
        self.server_host = server_host
        self.server_port = server_port
        self.chunk_queue = []  # 用于存储音频区块
        self.lock = threading.Lock()

        # 初始化 PyAudio
        self.pyaudio_instance = pyaudio.PyAudio()
        self.stream = self.pyaudio_instance.open(format=pyaudio.paInt16,
                                                  channels=channels,
                                                  rate=rate,
                                                  input=True,
                                                  input_device_index=self.device_index,
                                                  frames_per_buffer=max_chunk_size,
                                                  stream_callback=self.audio_callback)

        # 创建 TCP 连接
        self.client_socket = self.connect_to_server()

    def connect_to_server(self):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        while True:
            try:
                client_socket.connect((self.server_host, self.server_port))
                print("成功连接到服务器")
                return client_socket
            except Exception as e:
                logging.error(f"连接失败: {e}, 重新尝试连接...")
                time.sleep(5)  # 每5秒重试连接

    def start(self):
        self.stream.start_stream()
        print("音频捕获开始...")

    def audio_callback(self, in_data, frame_count, time_info, status):
        if status:
            print(status)

        # 将接收到的音频数据存储到队列中
        with self.lock:
            self.chunk_queue.append(in_data)

        # 如果队列中的数据足够，则发送数据到服务器
        if len(self.chunk_queue) >= 3:  # 两个块为一个完整音频发送
            send_data = b''.join(self.chunk_queue)
            self.client_socket.sendall(send_data)
            print("实时发送音频数据到服务器")
            self.chunk_queue.clear()  # 清空队列

        return (None, pyaudio.paContinue)

    def stop(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pyaudio_instance.terminate()
        self.client_socket.close()
        print("音频捕获停止。")

class SubtitleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("实时字幕")
        self.text_area = tk.Text(root, wrap=tk.WORD)
        self.text_area.pack(expand=True, fill=tk.BOTH)
        self.audio_capture = AudioCapture(device_index=1)  # 使用默认音频设备
        self.is_running = True

        # 启动音频捕获
        self.audio_capture.start()
        threading.Thread(target=self.receive_subtitles).start()  # 启动接收字幕线程

    def receive_subtitles(self):
        while self.is_running:
            try:
                response = self.audio_capture.client_socket.recv(4096).decode('utf-8')  # 接收服务器返回的字幕
                if response:
                    self.update_subtitle(response)  # 更新字幕
            except Exception as e:
                logging.error(f"接收数据时出错: {e}")
                self.audio_capture.stop()  # 连接出错，停止音频捕获

    def update_subtitle(self, text):
        self.text_area.insert(tk.END, text + "\n")
        self.text_area.see(tk.END)

    def stop(self):
        self.is_running = False
        self.audio_capture.stop()

root = tk.Tk()
app = SubtitleApp(root)

def on_closing():
    app.stop()
    root.destroy() 
    exit(0)

if __name__ == "__main__":
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

#python whisper_online_server.py --host 192.168.1.2 --port 43001 --warmup-file /root/whisper_streaming/jfk.wav -l INFO --lan zh --model tiny --task translate