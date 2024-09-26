import faster_whisper
from transformers import pipeline

for model in ["tiny", "small", "base"]:
    faster_whisper.download_model(model)

pipeline(
    "translation",
    model=f"Helsinki-NLP/opus-mt-en-es",
    device="cpu",
)
pipeline(
    "translation",
    model=f"Helsinki-NLP/opus-mt-es-en",
    device="cpu",
)
