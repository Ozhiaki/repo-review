"""Read an explicit, hash-checked tool bundle. Do not install or download here."""
from pathlib import Path

from . import records as r

NAMES = ("rg", "ast_grep", "node", "colgrep", "zoekt", "ctags")
MODEL_SHA256 = {
    "config.json": "c1413b20ad05927b8226aa2223b3ae104cd04c8541fe1300bdcf455fc8667601",
    "config_sentence_transformers.json": "34942289dec20e285b07132aa1d09980ed776a0bc34e531dd7b49c4701876871",
    "model.onnx": "ac5a92a685512b163c3c591438f518379309d2a98c4818a9c6e2986f789dc8ef",
    "model_int8.onnx": "eac35bdaa862e2762e6455337f7a3e704b05dbc4259f00929fcc8e10207f11c7",
    "onnx_config.json": "fa4fef89820dcdc33c5504c62c1d5efc19603cfbfebf02368a70d51a4dbe6651",
    "tokenizer.json": "a388b94942e98e5c661c6c23f919842285738bfd123a0d148dea0c56287505d0",
}


def load(path):
    path = Path(path).expanduser().resolve()
    value = r.read(path)
    r.require(value.get("version") == 1, "The tool bundle version is unsupported.")
    integrity = value["integrity"]
    r.require(isinstance(integrity, dict) and integrity, "The tool bundle has no integrity records.")
    for name, expected in integrity.items():
        target = path.parent / name
        r.require(not Path(name).is_absolute() and ".." not in Path(name).parts,
                  "An integrity path leaves the tool bundle.")
        r.require(target.is_file() and r.digest(target) == expected, "A tool bundle file differs: " + name)
    result = {}
    for name in (*NAMES, "cruiser"):
        relative = value[name]
        r.require(relative in integrity, "A tool has no integrity record: " + name)
        result[name] = str((path.parent / relative).resolve())
    model = path.parent / value["model"]
    r.require(model.is_dir() and any(name.startswith(value["model"] + "/") for name in integrity),
              "The tool bundle has no model records.")
    r.require(value.get("model_id") == "lightonai/LateOn-Code-edge", "The selected model ID differs.")
    r.require(value.get("model_revision") == "4bcdf5ed93f791259eb130b577a240f753d68dd8", "The selected model revision differs.")
    for name, expected in MODEL_SHA256.items():
        r.require(integrity.get(value["model"] + "/" + name) == expected, "The selected model weights differ: " + name)
    result["model"] = str(model.resolve())
    result["fingerprints"] = {str((path.parent / name).resolve()): expected for name, expected in integrity.items()}
    result["fingerprints"][str(path)] = r.digest(path)
    return result


def colgrep_environment(data, config):
    return dict(XDG_DATA_HOME=str(data), XDG_CONFIG_HOME=str(config), HF_HUB_OFFLINE="1",
                COLGREP_N_IVF_PROBE="8", COLGREP_N_FULL_SCORES="8192",
                COLGREP_CENTROID_SCORE_THRESHOLD="-1")
