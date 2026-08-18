"""Small JSON-over-gRPC helpers.

We use gRPC's generic handlers with JSON serialization so the project can run
without generated protobuf Python files. The wire transport is still gRPC.
A .proto contract is included in proto/ for future migration to protobuf.
"""
from __future__ import annotations

import json
from typing import Any


def dumps(value: Any) -> bytes:
    return json.dumps(value, separators=(",", ":"), default=str).encode("utf-8")


def loads(value: bytes) -> Any:
    return json.loads(value.decode("utf-8"))
