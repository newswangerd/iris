from collections import namedtuple
from dataclasses import dataclass, field
from typing import Optional, Callable, Any, List
from torch import multiprocessing as mp
import time

from enum import Enum


class RecorderState(Enum):
    LISTENING = 1
    RECORDING = 2
    OFFLINE = 3


class OutputChannel(Enum):
    TTS = 1
    SUB = 2


def default_timestamps() -> List[float]:
    return [0]


def default_suppress_tokens() -> List[int]:
    return [-1]


@dataclass
class VoiceChunkMsg:
    msg_lang: str
    target_lang: str
    audio: Any
    time_start: Optional[float] = field(default_factory=time.time)
    speaker: Optional[str] = None
    timestamps: List[float] = field(default_factory=default_timestamps)
    channel: OutputChannel = OutputChannel.SUB
    count: Optional[int] = 0


@dataclass
class TranscriptionMsg:
    msg_lang: str
    target_lang: str
    text: str
    time_start: Optional[float] = field(default_factory=time.time)
    speaker: Optional[str] = None
    channel: OutputChannel = OutputChannel.SUB


@dataclass
class TTSMsg:
    text: str
    time_start: Optional[float] = field(default_factory=time.time)


@dataclass
class Settings:
    model_path: str = "base"
    compute_type: str = "default"
    gpu_device_index: int = 0
    whisper_device: str = "cpu"
    translation_device: str = "cpu"
    tts_device: str = "cpu"
    beam_size: int = 5
    initial_prompt: Optional[str] = None
    suppress_tokens: List[int] = field(default_factory=default_suppress_tokens)
    external_lang: str = "en"
    user_lang: str = "en"
    sample_rate: int = 16000
    buffer_size: int = 512
    input_device_index: Optional[int] = None
    silero_threshold: float = 0.5


class ProcessArgs:
    def __init__(
        self,
        settings: Settings,
        ui_update_q: mp.Queue,
    ):
        # Settings
        self.settings = settings

        # Events
        self.pause_recording_event = mp.Event()
        self.shutdown_event = mp.Event()
        self.ready_event = mp.Event()
        self.is_tts_mode = mp.Event()

        # UI
        self.ui_update_q = ui_update_q
