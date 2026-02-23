import logging
from pathlib import Path

from faster_whisper import WhisperModel, BatchedInferencePipeline

from shared.config import config

logger = logging.getLogger(__name__)
model = WhisperModel(config.whisper.model)
batched_model = BatchedInferencePipeline(model=model)



def load(file_path: Path) -> str:
    segments, info = batched_model.transcribe(str(file_path), batch_size=config.whisper.batch_size)
    logger.debug("Transcription started for %s (language: %s, duration: %.1fs)",
                 file_path.name, info.language, info.duration)
    
    segments = list(segments)
    text = "".join(seg.text for seg in segments)
    logger.debug("Transcription completed for %s (total segments: %d, total text length: %d)",
                 file_path.name, len(segments), len(text))
    return text
