import torch.multiprocessing as mp
from transformers.models.fnet.tokenization_fnet import Dict
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

from threading import Thread


class MainThread(Thread):
    """
    TK really wants to be the main thread, but we need a place to coordinate all
    of the ML workers. This thread will handle all communication between the
    worker processes and the UI.
    """

    def __init__(
        self,
        args: ProcessArgs,
        worker_live_events,
        ui_update_q: mp.Queue,
        ui: UserInterface,
        tts_q: mp.Queue,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.args = args
        self.worker_live_events = worker_live_events
        self.ui_update_q = ui_update_q
        self.ui = ui
        self.tts_q = tts_q

        self.sub_translation = pipeline(
            "translation",
            model=f"Helsinki-NLP/opus-mt-{self.args.settings.external_lang}-{self.args.settings.user_lang}",
            device=self.args.settings.translation_device,
        )

    def set_tts_status(self, state):
        if state:
            self.ui.tts_label["text"] = "tts"
            self.args.is_tts_mode.set()
        else:
            self.ui.tts_label["text"] = "sub"
            self.args.is_tts_mode.clear()

    def toggle_tts(self):
        self.set_tts_status(not self.args.is_tts_mode.is_set())

    def set_recording_state(self, state: RecorderState):
        self.ui.set_recording_status(state)

    def add_transcription(self, msg: TranscriptionMsg):
        if not msg.text:
            return
        print(msg)

        if msg.msg_lang != self.args.settings.user_lang:
            text = self.sub_translation(msg.text)[0]["translation_text"]
        else:
            text = msg.text
        self.ui.add_subtitles("- " + msg.text)

        if msg.channel == OutputChannel.TTS:
            self.tts_q.put(
                TTSMsg(
                    text=msg.text,
                )
            )

    def run(self):
        msg: dict
        for msg in iter(self.ui_update_q.get, None):
            print(msg)
            for k, v in msg.items():
                getattr(self, k)(**v)


def main():
    print("Starting")
    settings = Settings(
        external_lang="en",
        user_lang="es",
        whisper_device="cpu",
        translation_device="cpu",
        tts_device="cpu",
        model_path="base",
        silero_threshold=0.5,
    )

    audio_out_q = mp.Queue()
    to_transcribe_q = mp.Queue()
    tts_q = mp.Queue()
    ui_update_q = mp.Queue()

    args = ProcessArgs(settings, ui_update_q)

    ui = UserInterface(ui_update_q)

    try:
        print("Initializing Workers")

        audio_start = mp.Event()
        whisper_start = mp.Event()
        # vad_start = mp.Event()
        tts_start = mp.Event()

        AudioWorker.start_process(to_transcribe_q, args, worker_intialized=audio_start)
        WhisperWorker.start_process(
            to_transcribe_q, args, worker_intialized=whisper_start
        )
        # VADWorker.start_process(
        #     audio_out_q,
        #     to_transcribe_q,
        #     args,
        #     worker_intialized=vad_start,
        # )
        TTSWorker.start_process(tts_q, args, worker_intialized=tts_start)

        while not all(
            [
                audio_start.is_set(),
                whisper_start.is_set(),
                # vad_start.is_set(),
                tts_start.is_set(),
            ]
        ):
            time.sleep(1)

        MainThread(args, [], ui_update_q, ui, tts_q).start()

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
