"""Hash stored bytes and link targets without following links."""
import hashlib
import os
from pathlib import Path
import stat

from prepass_runtime import records as r


def tree(root):
    root = Path(root)
    r.require(root.is_dir() and not root.is_symlink(), "The artifact directory is absent or linked.")
    result = {}
    for here, directories, files in os.walk(root, followlinks=False):
        directories.sort()
        for name in sorted(directories + files):
            path = Path(here) / name
            if name == ".DS_Store":
                continue
            mode = path.lstat().st_mode
            relative = path.relative_to(root).as_posix()
            if stat.S_ISLNK(mode):
                result[relative] = "symlink:" + hashlib.sha256(os.readlink(os.fsencode(path))).hexdigest()
            elif stat.S_ISREG(mode):
                result[relative] = r.digest(path)
            else:
                r.require(stat.S_ISDIR(mode), "A stored artifact is not a file, link, or directory.")
    return result
