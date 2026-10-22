"""Static import evidence. Never import or execute a subject module."""
from __future__ import annotations

import ast
from collections import defaultdict
import hashlib
from pathlib import Path
import tokenize


LIMITS = [
    "The map shows source candidates, not the runtime import graph.",
    "Import roots are explicit. Runtime sys.path changes are not resolved.",
    "Conditional imports are retained. Their conditions are not evaluated.",
    "An imported member can be an attribute or a submodule.",
    "Dynamic calls are recorded without adding resolved edges.",
    "Import hooks, exec, eval, and aliased dynamic calls can add other imports.",
    "External and missing imports are not distinguished without an environment.",
]


def build(root, files, import_roots):
    root = Path(root)
    files = sorted(set(files))
    selected = set(files)
    index = defaultdict(set)
    for name in files:
        path = Path(name)
        for base in import_roots:
            try:
                rel = path.relative_to(base)
            except ValueError:
                continue
            parts = list(rel.with_suffix("").parts)
            if parts[-1] == "__init__":
                parts.pop()
            if parts and all(part.isidentifier() for part in parts):
                index[".".join(parts)].add(name)

    def resolve(module):
        candidates = sorted(index.get(module, ()))
        if len(candidates) == 1:
            return candidates, "local_candidate"
        if candidates:
            return candidates, "ambiguous"
        # A namespace package has no source file of its own.
        if any(key.startswith(module + ".") for key in index) and module:
            return [], "namespace"
        return [], "unresolved"

    records, errors, file_records = [], [], []
    edges = set()
    for name in files:
        path = root / name
        info = dict(path=name, status="parsed", sha256=None)
        try:
            info["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
            with tokenize.open(path) as stream:
                text = stream.read()
            tree = ast.parse(text, filename=name)
        except (OSError, SyntaxError, UnicodeError, LookupError) as exc:
            info["status"] = "error"
            errors.append(dict(path=name, kind=type(exc).__name__, message=str(exc),
                               line=getattr(exc, "lineno", None), column=getattr(exc, "offset", None)))
            file_records.append(info)
            continue
        file_records.append(info)
        for node in sorted(ast.walk(tree), key=lambda n: (getattr(n, "lineno", 0), getattr(n, "col_offset", 0))):
            common = dict(path=name, start_line=getattr(node, "lineno", 0),
                          end_line=getattr(node, "end_lineno", 0),
                          start_byte_column=getattr(node, "col_offset", 0),
                          end_byte_column=getattr(node, "end_col_offset", 0))
            if isinstance(node, ast.Call):
                func = node.func
                dynamic = (isinstance(func, ast.Name) and func.id == "__import__") or (
                    isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name)
                    and func.value.id == "importlib" and func.attr == "import_module")
                if dynamic:
                    arg = node.args[0] if node.args else None
                    literal = arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None
                    records.append(dict(**common, kind="dynamic", module=literal,
                                        expression=ast.get_source_segment(text, node),
                                        status="dynamic_unresolved", targets=[], candidates=[]))
                continue
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            for alias in node.names:
                record = dict(**common, kind="import" if isinstance(node, ast.Import) else "from",
                              name=alias.name, alias=alias.asname, targets=[], candidates=[])
                if isinstance(node, ast.Import):
                    module = alias.name
                    candidates, status = resolve(module)
                    record.update(module=module, status=status, candidates=candidates)
                    if status == "local_candidate":
                        record["targets"] = candidates
                else:
                    base = node.module or ""
                    # Relative imports use the physical package location. The
                    # selected roots bound traversal; roots themselves are not packages.
                    if node.level:
                        parent = Path(name).parent
                        applicable = [Path(p) for p in import_roots if parent == Path(p) or Path(p) in parent.parents]
                        boundary = max(applicable, key=lambda p: len(p.parts)) if applicable else Path(".")
                        package_depth = len(parent.relative_to(boundary).parts)
                        if node.level > package_depth:
                            record.update(module="." * node.level + base, status="relative_outside_root")
                            records.append(record)
                            continue
                        for _ in range(node.level - 1):
                            parent = parent.parent
                        physical = parent.joinpath(*base.split(".")) if base else parent
                        variants = [str(physical.with_suffix(".py")), str(physical / "__init__.py")]
                        bases = sorted(set(variants) & selected)
                        child = physical / alias.name
                        children = sorted({str(child.with_suffix(".py")), str(child / "__init__.py")} & selected) if alias.name != "*" else []
                        status = "local_candidate" if bases or children else "unresolved"
                        candidates = sorted(set(bases + children))
                        module = "." * node.level + base
                        ambiguous = len(bases) > 1 or len(children) > 1
                    else:
                        module = base
                        bases, status = resolve(base)
                        children, child_status = resolve(base + "." + alias.name) if alias.name != "*" else ([], "wildcard")
                        candidates = sorted(set(bases + children))
                        ambiguous = status == "ambiguous" or child_status == "ambiguous"
                        if children and child_status == "local_candidate":
                            status = "local_candidate"
                    if ambiguous:
                        record.update(module=module, status="ambiguous", candidates=candidates)
                    else:
                        record.update(module=module, status=status, candidates=candidates, targets=candidates)
                    record["member_status"] = "submodule_candidate" if children else (
                        "wildcard_unexpanded" if alias.name == "*" else "attribute_or_missing_submodule")
                records.append(record)
                for target in record["targets"]:
                    edges.add((name, target))
    reverse = {name: [] for name in files}
    for source, target in sorted(edges):
        reverse[target].append(source)
    return dict(files=file_records, imports=records, errors=errors,
                edges=[list(edge) for edge in sorted(edges)],
                reverse={key: sorted(set(value)) for key, value in reverse.items()},
                import_roots=import_roots, limits=LIMITS)
