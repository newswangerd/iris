import io
from mutagen.ogg import OggPage
import pyogg
import torch
from fastapi import WebSocket
import numpy as np

from collections import deque

from typing import Optional


from iris.server.models import (
    StreamMessage,
    TranscriptionMessage,
    User
)

from iris.server import audio_in_q

from iris.server.vad import VADHandler

SAMPLE_RATE = 16000
SAMPLES_PER_MS = int(SAMPLE_RATE / 1000)

# Silero chunks are 32 ms and 16 bits each (2 bytes)
BYTES_PER_SILERO_FRAME = SAMPLES_PER_MS * 32 * 2


def process_stream(sound):
    audio_int16 = np.frombuffer(sound, np.int16)
    abs_max = np.abs(audio_int16).max()
    sound = audio_int16.astype(np.float32)
    if abs_max > 0:
        sound *= 1 / 32768
    sound = sound.squeeze()
    return sound


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def arrange_frames(frames: bytearray):
    """
    The javacript library on the frontend only supports frames that are multiples of 20ms.
    Silero VAD requires 32ms frames. This function takes the output from the decoded OGG
    page and converts the 20ms frames into 32ms frames.
    """

    if len(frames) == 0:
        return [], None

    new_frames = [frame for frame in chunks(frames, BYTES_PER_SILERO_FRAME)]
    if len(new_frames[-1]) != BYTES_PER_SILERO_FRAME:
        remainder = new_frames.pop()
    else:
        remainder = None

    return new_frames, remainder


def decode(data, opus_decoder, leftover_bits: Optional[bytearray] = None):
    bin = io.BytesIO(data["bytes"])
    bin.seek(0)

    if not leftover_bits:
        frames = bytearray()
    else:
        frames = leftover_bits

    for p in OggPage(bin).packets:
        if p.startswith(b"Opus"):
            continue
        frames.extend(bytearray(opus_decoder.decode(bytearray(p))))

    return arrange_frames(frames)


async def receive_stream(websocket: WebSocket, user: User):
    is_streaming = False
    recording_meta = None
    opus_decoder = pyogg.OpusDecoder()
    opus_decoder.set_channels(1)
    opus_decoder.set_sampling_frequency(SAMPLE_RATE)

    vad_model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad", model="silero_vad"
    )

    remainder = None
    buffer = deque()

    def transcribe(audio):
        print("TRANSCRIBING")
        audio_in_q.put(TranscriptionMessage(audio=audio, user=user, recording_meta=recording_meta))

    vad = VADHandler(on_data_ready=transcribe)

    while True:
        data = await websocket.receive()
        websocket.state

        if "text" in data:
            action, stream_meta = data["text"].split(":", maxsplit=1)

            stream_meta = StreamMessage.model_validate_json(stream_meta)

            if action == "START":
                print("start stream")
                is_streaming = True
                remainder = None
                buffer = deque()

            elif action == "CANCEL":
                is_streaming = False
                recording_meta = None
                await websocket.send_json({})

            elif action == "STOP":
                is_streaming = False
                recording_meta = None

                await websocket.send_json({})

                print("end stream")

        elif is_streaming:
            frames, remainder = decode(data, opus_decoder, leftover_bits=remainder)

            for frame in frames:
                vad.vad(frame)
