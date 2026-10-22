"""Observe delivered Claude Code tool results. No model client or launcher."""
from pathlib import Path
import json

from prepass_runtime import records as r


def objects(value):
    if isinstance(value, str):
        try:
            yield from objects(json.loads(value))
        except (ValueError, RecursionError):
            return
    elif isinstance(value, list):
        for item in value:
            yield from objects(item)
    elif isinstance(value, dict):
        if "delivery_id" in value and "source" in value:
            yield value
        elif value.get("type") == "text":
            yield from objects(value.get("text"))
        elif "content" in value and not value.get("isError"):
            yield from objects(value["content"])


class Observer:
    """Called by a trusted host on events it actually delivered to the agent."""

    def __init__(self, home, session):
        self.home = Path(home).resolve()
        self.session = session
        self.tools = {}

    def event(self, event):
        if event.get("session_id"):
            r.require(event["session_id"] == self.session, "A host event has a different session ID.")
        if event.get("type") == "assistant":
            for block in event.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    self.tools[block["id"]] = block["name"]
        if event.get("type") != "user":
            return
        content = event.get("message", {}).get("content", [])
        if not isinstance(content, list):
            return
        for block in content:
            if block.get("type") != "tool_result" or block.get("is_error") or block.get("truncated"):
                continue
            if self.tools.get(block.get("tool_use_id")) != "mcp__review__read_source":
                continue
            for item in objects(block.get("content")):
                self.capture(item, event)

    def capture(self, item, event):
        identifier = item.get("delivery_id")
        r.require(isinstance(identifier, str) and len(identifier) == 32
                  and all(c in "0123456789abcdef" for c in identifier), "A delivered source ID is invalid.")
        original = r.read(self.home / "produced" / (identifier + ".json"))
        r.require(isinstance(item.get("source"), str), "The delivered source text is absent.")
        if item.get("truncated") or original["truncated"]:
            return
        data = item["source"].encode("utf-8")
        import hashlib
        r.require(len(data) == original["produced_bytes"]
                  and hashlib.sha256(data).hexdigest() == original["produced_sha256"],
                  "The host source response differs from the produced delivery.")
        target = self.home / "captures" / (identifier + ".bin")
        r.output_directory(target.parent)
        r.require(not target.is_symlink(), "A host capture is linked.")
        if target.exists():
            r.require(target.read_bytes() == data, "The host repeated conflicting source bytes.")
        else:
            target.write_bytes(data)
        r.save(self.home / "delivered" / (identifier + ".json"), {
            "id": identifier, "capture": str(target), "session_id": self.session,
            "host_event_sha256": r.hashed_json(event), "boundary": "claude_code_user_tool_result",
        })
