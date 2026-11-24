#!/usr/bin/env python3
import sys, base64, pathlib
xfer = pathlib.Path(sys.argv[1])
prefix = sys.argv[2]
out = pathlib.Path(sys.argv[3])
parts = sorted(xfer.glob(prefix + "*.txt"))
if not parts:
    raise SystemExit(f"no parts {prefix}")
data = b"".join(base64.b64decode(p.read_text().strip()) for p in parts)
out.write_bytes(data)
print(f"wrote {out} bytes={len(data)} from {len(parts)} parts")
