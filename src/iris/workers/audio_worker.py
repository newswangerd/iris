import pyaudio
import traceback
import logging
from iris.data_types import ProcessArgs
from iris.workers.base_worker import IRISWorker


class AudioWorker(IRISWorker):
    def __init__(self, audio_queue, args: ProcessArgs):
        self.audio_queue = audio_queue
        self.args = args
        self.audio_interface = pyaudio.PyAudio()
        if self.args.settings.input_device_index is None:
            default_device = self.audio_interface.get_default_input_device_info()
            input_device_index = default_device["index"]
        self.stream = self.audio_interface.open(
            rate=self.args.settings.sample_rate,
            format=pyaudio.paInt16,
            channels=1,
            input=True,
            frames_per_buffer=self.args.settings.buffer_size,
            input_device_index=self.args.settings.input_device_index,
        )

    def _run(self) -> None:
        try:
            while not self.args.shutdown_event.is_set():
                try:
                    data = self.stream.read(self.args.settings.buffer_size)

                except OSError as e:
                    if e.errno == pyaudio.paInputOverflowed:
                        logging.warning("Input overflowed. Frame dropped.")
                    else:
                        logging.error(f"Error during recording: {e}")
                    tb_str = traceback.format_exc()
                    print(f"Traceback: {tb_str}")
                    print(f"Error: {e}")
                    continue

                except Exception as e:
                    logging.error(f"Error during recording: {e}")
                    tb_str = traceback.format_exc()
                    print(f"Traceback: {tb_str}")
                    print(f"Error: {e}")
                    continue

                self.audio_queue.put(data)

        except KeyboardInterrupt:
            logging.debug(
                "Audio data worker process " "finished due to KeyboardInterrupt"
            )
        finally:
            self.stream.stop_stream()
            self.stream.close()
            self.audio_interface.terminate()
