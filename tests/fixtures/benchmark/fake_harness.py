#!/usr/bin/env python3
"""Emit deterministic Codex or Pi telemetry for benchmark runner tests."""

import json
import os
import pathlib
import sys
import time


mode = os.environ.get("WEFT_BENCHMARK_FAKE_MODE", "ok")
if "--version" in sys.argv:
    print("fake-harness 1.0")
    raise SystemExit(0)
if mode == "auth":
    print("authentication required", file=sys.stderr)
    raise SystemExit(2)
if mode == "timeout":
    time.sleep(5)

args = sys.argv[1:]
is_pi = "--mode" in args
has_skill = any(
    path.name == "SKILL.md" for path in pathlib.Path.cwd().rglob("SKILL.md")
)
answer = "Used Weft. Verified result." if has_skill else "Generic result."

if is_pi:
    model = args[args.index("--model") + 1]
    provider, model_id = model.split("/", 1)
    message = {
        "type": "message_end",
        "message": {
            "role": "assistant",
            "content": [{"type": "text", "text": answer}],
            "provider": provider,
            "model": model_id,
        },
    }
    if mode != "missing_tokens":
        message["message"]["usage"] = {"input": 90 if has_skill else 60, "output": 10}
    print(json.dumps({"type": "session", "version": 3}))
    print(json.dumps(message))
else:
    print(
        json.dumps(
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": answer},
            }
        )
    )
    completed = {"type": "turn.completed"}
    if mode != "missing_tokens":
        completed["usage"] = {
            "input_tokens": 90 if has_skill else 60,
            "output_tokens": 10,
        }
    print(json.dumps(completed))
