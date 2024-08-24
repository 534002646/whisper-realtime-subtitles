FROM nvidia/cuda:12.0.0-devel-ubuntu20.04

WORKDIR /root

RUN apt-get update -y && apt-get install -y python3 python3-pip libcudnn8 libcudnn8-dev
RUN python3 -m pip install pip --upgrade
COPY jfk.wav /root/
COPY line_packet.py /root/
COPY whisper_online_server.py /root/
COPY whisper_online.py /root/
COPY silero_vad.py /root/
RUN pip3 install faster-whisper
RUN pip install librosa soundfile opus-fast-mosestokenizer

CMD python3 /root/whisper_online_server.py --host 0.0.0.0 --port 43001 --buffer_trimming sentence --warmup-file /root/jfk.wav -l DEBUG --model base --task transcribe --lan zh --min-chunk-size 2 --backend faster-whisper 
