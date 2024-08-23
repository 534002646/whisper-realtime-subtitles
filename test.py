
import sounddevice as sd
import pyaudio


def main():
    print(sd.query_devices())
    p = pyaudio.PyAudio()

    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        print(f"设备 {i}: {info['name']} - 最大输入通道: {info['maxInputChannels']}, 最大输出通道: {info['maxOutputChannels']}, 支持的采样率: {info['defaultSampleRate']}")

if __name__ == "__main__":
    main()