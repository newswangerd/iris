from diart import SpeakerDiarization, SpeakerDiarizationConfig
from diart.sources import MicrophoneAudioSource
from diart.inference import StreamingInference
from diart.sinks import RTTMWriter
# from diart.models import SegmentationModel
import os

import torch



cfg = SpeakerDiarizationConfig(device=torch.device("cpu"), delta_new=0.57)
pipeline = SpeakerDiarization(cfg)
mic = MicrophoneAudioSource()
inference = StreamingInference(pipeline, mic, do_plot=True)
inference.attach_observers(RTTMWriter(mic.uri, "./file.rttm"))
prediction = inference()
