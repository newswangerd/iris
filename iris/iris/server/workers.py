import asyncio
from threading import Thread

from torch import multiprocessing as mp

from iris.server import MessageBroker, settings
from iris.server.models import Message, TranscriptionMessage
from iris.server.transcription import Transcriber, Translator


class BrokerThread(Thread):
    def __init__(self, whisper_out: mp.Queue, broker: MessageBroker, **kwargs):
        print("Starting broker")
        super().__init__(**kwargs)

        self.broker = broker
        self.whisper_out = whisper_out
        self.translator = Translator()
        print("Broker online")

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(self.a_run())
        loop.close()

    async def a_run(self):
        msg: Message
        for msg in iter(self.whisper_out.get, None):
            if msg.is_accepted:
                await self.translate_and_send(msg)
            else:
                await self.broker.send(msg.json())

    async def translate_and_send(self, m: Message):
        print("adding translation")
        if m.language == settings.base_language:
            for lang in settings.supported_languages:
                m.translated_text[lang] = self.translator.translate(
                    m.text, (m.language, lang)
                )
        else:
            m.translated_text[settings.base_language] = self.translator.translate(
                m.text,
                (m.language, settings.base_language),
            )

        await self.broker.send(m.json())
        m.save_to_file()
        m.save_to_log()


def whisper_process(audio_in_q: mp.Queue, out_q: mp.Queue):
    print("Starting transcriber")
    transcriber = Transcriber()
    print("Transcriber online")

    msg: TranscriptionMessage
    try:
        for msg in iter(audio_in_q.get, None):
            m = transcriber.transcribe(msg)
            if m:
                out_q.put(m)
    except KeyboardInterrupt:
        exit()
