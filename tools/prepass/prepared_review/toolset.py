"""Record explicit local static tools. No installer, model weights, or indexes."""
from pathlib import Path
import shutil

from prepass_runtime import records as r
from .artifacts import tree


def support_tree(home):
    home = Path(home)
    for path in home.rglob("*"):
        if path.is_symlink():
            r.require(path.resolve().is_relative_to(home.resolve()), "A tool support link leaves its recorded directory.")
    return tree(home)


def executable(value):
    found = shutil.which(str(value))
    r.require(found is not None, "An installed tool is absent: " + str(value))
    return Path(found).resolve()


def load(path):
    path = Path(path).expanduser().resolve()
    value = r.read(path)
    r.require(value.get("kind") == "prepared-review-tools-v1", "Use a Prepared Review tool manifest.")
    files = value["files"]
    directories = value.get("trees", {})
    r.require(isinstance(files, dict) and files, "The tool manifest has no file hashes.")
    r.require(all(Path(name).is_absolute() and Path(name).is_file() and r.digest(name) == sha
                  for name, sha in files.items()), "A recorded static tool file changed.")
    r.require(all(Path(name).is_absolute() and r.hashed_json(support_tree(name)) == sha
                  for name, sha in directories.items()), "A recorded tool directory changed.")
    tools = value["tools"]
    r.require(set(tools) in ({"rg", "ast_grep"}, {"rg", "ast_grep", "node", "cruiser"}),
              "Supply rg and ast-grep, with an optional Node/dependency-cruiser pair.")
    r.require(all(name in files for name in tools.values()), "A tool has no recorded file hash.")
    if "cruiser" in tools:
        r.require(any(Path(tools["cruiser"]).is_relative_to(Path(home)) for home in directories),
                  "Record the dependency-cruiser node_modules directory.")
    return dict(tools, fingerprints=dict(files, **{str(path): r.digest(path)}), tree_fingerprints=directories)


def create(args):
    from .cli import PROJECT, protected_output
    tools = {"rg": executable(args.rg), "ast_grep": executable(args.ast_grep)}
    trees = {}
    r.require(bool(args.node) == bool(args.node_modules), "Supply both --node and --node-modules.")
    if args.node:
        home = args.node_modules.expanduser().resolve()
        tools.update(node=executable(args.node), cruiser=home / "dependency-cruiser/bin/dependency-cruise.mjs")
        r.require(r.read(home / "dependency-cruiser/package.json")["version"] == "17.3.3",
                  "Use dependency-cruiser 17.3.3 for the retained import policy.")
        r.require(r.read(home / "typescript/package.json")["version"] == "5.9.3", "Use TypeScript 5.9.3.")
        trees[str(home)] = r.hashed_json(support_tree(home))
    output = protected_output(args.out, [PROJECT, *tools.values(), *trees])
    r.output_directory(output)
    commands = r.Commands(output / "commands", 120, 30)
    versions = {}
    try:
        for name in ("rg", "ast_grep", "node"):
            if name in tools:
                result = commands.run(name + "-version", [tools[name], "--version"], output)
                versions[name] = result["stdout"].decode("utf-8").splitlines()[0]
        r.require(versions["rg"].startswith("ripgrep 15.1.0"), "Use ripgrep 15.1.0 for the retained text policy.")
        r.require(versions["ast_grep"] == "ast-grep 0.41.1", "Use ast-grep 0.41.1 for the retained outline policy.")
        if "node" in versions:
            r.require(versions["node"] == "v22.23.3", "Use Node 22.23.3 for the retained import policy.")
        files = {str(path): r.digest(path) for path in tools.values()}
        r.save(output / "tools.json", dict(kind="prepared-review-tools-v1", tools={k: str(v) for k, v in tools.items()},
                                           files=files, trees=trees, versions=versions))
        load(output / "tools.json")
    finally:
        commands.stop()
    r.say("Tool manifest: " + str(output / "tools.json"))
    return 0
