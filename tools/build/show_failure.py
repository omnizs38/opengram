#!/usr/bin/env python3
"""Print bounded failure diagnostics; keep the full, redacted log as an artifact."""
from collections import deque
import os
from pathlib import Path
import re
import sys
import tempfile

ERROR = re.compile(r"\b(?:fatal\s+error|error|failed|failure|traceback|assertionerror)\b", re.I)
MAX_ERRORS = 15
TAIL_LINES = 35
LINE_WIDTH = 240


def report(path):
    path = Path(path)
    secrets = sorted({os.environ[key] for key in ("API_ID", "API_HASH")
                      if os.environ.get(key)}, key=len, reverse=True)
    errors = []
    tail = deque(maxlen=TAIL_LINES)
    temporary = None
    try:
        # Redact the artifact too: Actions' console masking does not cover files.
        with path.open(encoding="utf-8", errors="replace") as source, tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, delete=False
        ) as target:
            temporary = Path(target.name)
            for number, line in enumerate(source, 1):
                for secret in secrets:
                    line = line.replace(secret, "***")
                target.write(line)
                short = line.rstrip()[:LINE_WIDTH]
                item = (number, short)
                tail.append(item)
                if len(errors) < MAX_ERRORS and ERROR.search(short):
                    errors.append(item)
        temporary.replace(path)
    except OSError as exc:
        print(f"::error::Failed to read or sanitize {path.name}: {exc}")
        # Do not leave an unsanitized log eligible for artifact upload.
        path.unlink(missing_ok=True)
        return 1
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

    print(f"::error::Step failed. Short diagnostics below; full log: {path.name} artifact.")
    print("First matching errors (up to 15):")
    for number, line in errors:
        print(f"  {number}: {line}")
    if not errors:
        print("  No explicit error line found; inspect the tail below.")
    print("Last 35 lines:")
    for number, line in tail:
        print(f"  {number}: {line}")
    return 0


if __name__ == "__main__":
    sys.exit(report(sys.argv[1]))
