import torch.multiprocessing as mp
from iris.workers import WhisperWorker, VADWorker, AudioWorker, TTSWorker
from iris.data_types import (
    ProcessArgs,
    Settings,
    OutputChannel,
    TranscriptionMsg,
    TTSMsg,
    RecorderState,
)
import time
from transformers import pipeline
from iris.gui import UserInterface


def main():
    print("Starting")
    settings = Settings(
        external_lang="ru",
        user_lang="en",
        whisper_device="cpu",
        translation_device="mps",
        tts_device="cpu",
    )

    audio_out_q = mp.Queue()
    to_transcribe_q = mp.Queue()
    tts_q = mp.Queue()
    ui_update_q = mp.Queue()

    sub_translation = pipeline(
        "translation",
        model=f"Helsinki-NLP/opus-mt-{settings.external_lang}-{settings.user_lang}",
        device=settings.translation_device,
    )

    args = ProcessArgs(settings, ui_update_q)

    ui = UserInterface(tts_q, sub_translation, args, ui_update_q)

    def transcription_callback(msg: TranscriptionMsg):
        ui.transcription_callback(msg)

    def recording_state_callback(state: RecorderState):
        ui.set_recording_status(state)

    try:
        print("Initializing Workers")

        audio_start = mp.Event()
        whisper_start = mp.Event()
        vad_start = mp.Event()
        tts_start = mp.Event()

        AudioWorker.start_process(audio_out_q, args, worker_intialized=audio_start)
        WhisperWorker.start_process(
            to_transcribe_q, args, worker_intialized=whisper_start
        )
        VADWorker.start_process(
            audio_out_q,
            to_transcribe_q,
            args,
            worker_intialized=vad_start,
        )
        TTSWorker.start_process(tts_q, args, worker_intialized=tts_start)

        while not all(
            [
                audio_start.is_set(),
                whisper_start.is_set(),
                vad_start.is_set(),
                tts_start.is_set(),
            ]
        ):
            time.sleep(1)

        print("Ready")

        ui.run()

    except KeyboardInterrupt:
        pass
    finally:
        args.shutdown_event.set()
        audio_out_q.close()
        to_transcribe_q.close()
        ui_update_q.close()
        tts_q.close()


if __name__ == "__main__":
    main()
