"""Token limits use the same encoding as the retained source exporter."""
from functools import lru_cache
from importlib.metadata import version
from pathlib import Path

from . import records as r


def identity():
    import tiktoken
    r.require(version("tiktoken") == "0.12.0", "Use tiktoken 0.12.0 for the retained token policy.")
    home = Path(tiktoken.__file__).resolve().parent
    files = [*home.glob("*.py"), *home.glob("*.so"), *home.glob("*.pyd")]
    return {str(path): r.digest(path) for path in files}


@lru_cache(maxsize=1)
def encoding():
    import tiktoken
    r.require(version("tiktoken") == "0.12.0", "Use tiktoken 0.12.0 for the retained token policy.")
    return tiktoken.get_encoding("o200k_base")


def tokens(text):
    return len(encoding().encode(text, disallowed_special=()))


def bounded(lines, limit, marker):
    result = []
    for index, line in enumerate(lines):
        suffix = [] if index == len(lines) - 1 else [marker]
        if tokens("\n".join(result + [line] + suffix) + "\n") > limit:
            return result + [marker]
        result.append(line)
    return result
