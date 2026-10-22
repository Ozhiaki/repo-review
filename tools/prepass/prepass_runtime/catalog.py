"""The retained language tables and broad text patterns."""
import os
import re

LANG_BY_EXT = {
    ".rs": "Rust", ".py": "Python", ".pyi": "Python", ".ts": "TypeScript",
    ".tsx": "TypeScript", ".js": "JavaScript", ".jsx": "JavaScript",
    ".mjs": "JavaScript", ".cjs": "JavaScript", ".go": "Go", ".java": "Java",
    ".kt": "Kotlin", ".swift": "Swift", ".c": "C", ".h": "C/C++ header",
    ".cc": "C++", ".cpp": "C++", ".hpp": "C++", ".cu": "CUDA", ".rb": "Ruby",
    ".php": "PHP", ".cs": "C#", ".scala": "Scala", ".lua": "Lua",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell", ".sql": "SQL",
    ".md": "Markdown", ".rst": "reStructuredText", ".txt": "Text",
    ".toml": "TOML", ".yaml": "YAML", ".yml": "YAML", ".json": "JSON",
    ".lock": "Lockfile", ".nix": "Nix", ".html": "HTML", ".css": "CSS",
    ".proto": "Protobuf", ".zig": "Zig", ".ex": "Elixir", ".exs": "Elixir",
}


NAME_LANG = {"Makefile": "Makefile", "Dockerfile": "Dockerfile", "justfile": "Just"}


DOC_LANGS = {"Markdown", "reStructuredText", "Text"}


DATA_LANGS = {"TOML", "YAML", "JSON", "Lockfile", "Nix", "HTML", "CSS", "Protobuf"}


OUTLINE_KINDS = {
    "rust": ["function_item", "function_signature_item", "struct_item", "enum_item",
             "union_item", "trait_item", "impl_item", "mod_item", "type_item",
             "const_item", "static_item", "macro_definition"],
    "python": ["function_definition", "class_definition"],
    "typescript": ["function_declaration", "class_declaration", "abstract_class_declaration",
                   "method_definition", "interface_declaration", "type_alias_declaration",
                   "enum_declaration"],
    "tsx": ["function_declaration", "class_declaration", "method_definition",
            "interface_declaration", "type_alias_declaration", "enum_declaration"],
    "javascript": ["function_declaration", "class_declaration", "method_definition"],
    "go": ["function_declaration", "method_declaration", "type_spec"],
    "java": ["class_declaration", "interface_declaration", "enum_declaration",
             "record_declaration", "method_declaration", "constructor_declaration"],
}


SG_LANG_BY_EXT = {".rs": "rust", ".py": "python", ".ts": "typescript", ".tsx": "tsx",
                  ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
                  ".go": "go", ".java": "java"}


RISK = [
    ("process-spawn", r"Command::new|std::process::|subprocess\.|os\.system\(|os\.popen\(|child_process|execSync|execFile|\bspawn\(|exec\.Command|ProcessBuilder|Runtime\.getRuntime"),
    ("file-write-delete", r"fs::write|File::create|OpenOptions|\.write_all\(|fs::remove_|remove_dir_all|fs::rename|fs::copy|\.persist\(|open\([^)]*['\"][wa]b?['\"]|writeFile|\.write_text\(|\.write_bytes\(|shutil\.(rmtree|move|copy)|os\.remove\(|os\.unlink\(|\.unlink\(|os\.WriteFile|os\.Create\(|os\.Remove"),
    ("network", r"reqwest|hyper::|TcpStream|TcpListener|UdpSocket|\bureq\b|https?://|urllib|requests\.(get|post|put|delete|Session)|httpx|aiohttp|socket\.socket|\bfetch\(|axios|net/http|net\.Dial|hf_hub|huggingface"),
    ("unsafe-ffi", r"\bunsafe\b|transmute|from_raw_parts|from_raw\(|\*mut |#\[no_mangle\]|extern \"C\"|ctypes|cffi|\bdlopen\b"),
    ("eval-dynamic-load", r"\beval\(|\bexec\(|new Function\(|__import__|importlib\.import_module|libloading|Library::new|load_dynamic"),
    ("deserialize", r"serde_json::from_|toml::from_str|serde_yaml::from|bincode::|rmp_serde::|postcard::|ciborium|pickle\.loads?\(|yaml\.load\(|marshal\.loads?\(|json\.loads?\(|JSON\.parse|np\.load\(|json\.Unmarshal|\.unmarshal\("),
    ("env-input", r"std::env::var|env::var\(|env::args|os\.environ|os\.getenv|process\.env|os\.Getenv"),
    ("ignored-result", r"let _ =|\.ok\(\);|\.unwrap_or_default\(\)|except\s*:\s*pass|except Exception\s*:\s*pass|catch\s*\([^)]*\)\s*\{\s*\}|_ = err"),
]


PANIC_PATTERN = r"\.unwrap\(\)|\.expect\(|panic!\(|unreachable!\(|todo!\(|unimplemented!\("


TEST_PATH = re.compile(r"(^|/)(tests?|__tests__|spec|testdata|fixtures)/|(^|/)test_[^/]*\.py$|_test\.(py|go|rs)$|\.(test|spec)\.[jt]sx?$|(^|/)conftest\.py$|(^|/)benches/")


def lang_of(path):
    name = os.path.basename(path)
    if name in NAME_LANG:
        return NAME_LANG[name]
    return LANG_BY_EXT.get(os.path.splitext(name)[1].lower(), "Other")
