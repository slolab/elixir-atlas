import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from starlette.responses import Response


async def trace(request, call_next):
    request.state.request_id = uuid.uuid4().hex
    directory = request.app.state.trace_directory
    if not directory or not request.url.path.startswith("/api/"):
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response
    started = time.monotonic()
    body = await request.body()
    response = await call_next(request)
    content = b"".join([part async for part in response.body_iterator])
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    filename = request.state.request_id + ".json"
    (directory / filename).write_bytes(content)
    try:
        body = json.loads(body) if body else None
    except ValueError:
        body = body.decode(errors="replace")
    entry = {"request_id": request.state.request_id, "time": datetime.now(timezone.utc).isoformat(), "method": request.method,
             "url": str(request.url), "body": body, "status": response.status_code, "response_file": filename,
             "response_bytes": len(content), "duration_ms": round((time.monotonic() - started) * 1000, 2)}
    with (directory / "requests.jsonl").open("a") as stream:
        stream.write(json.dumps(entry) + "\n")
    return Response(content, status_code=response.status_code, headers={**response.headers, "X-Request-ID": request.state.request_id}, background=response.background)
