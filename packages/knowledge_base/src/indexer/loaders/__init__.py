from pathlib import Path

from indexer.loaders import audio, pdf, text

LOADERS = {
    ".pdf": pdf.load,
    ".mp3": audio.load,
    ".mp4": audio.load,
    ".txt": text.load,
    ".md": text.load,
    ".markdown": text.load,
    ".rst": text.load,
}

SUPPORTED_EXTENSIONS = set(LOADERS.keys())


def load(file_path: Path) -> str:
    """Load a file and return its text content. Raises ValueError for unsupported types."""
    loader = LOADERS.get(file_path.suffix.lower())
    if loader is None:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")
    return loader(file_path)
