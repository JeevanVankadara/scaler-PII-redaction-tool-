"""REST API for the redactor, and the server for the built interface.

Local:   python -m server.app
Render:  gunicorn server.app:app  (see Dockerfile)
"""

import os
import sys
from pathlib import Path

from flask import Flask, abort, jsonify, request, send_file, send_from_directory

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.jobs import JobStore  # noqa: E402

DIST = ROOT / "web" / "dist"
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
store = JobStore()


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/jobs")
def create_job():
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        abort(400, "no file uploaded")
    if not upload.filename.lower().endswith(".docx"):
        abort(400, "only .docx files are accepted")

    job = store.create(Path(upload.filename).name, upload)
    return jsonify(job.summary()), 202


@app.get("/api/jobs/<job_id>")
def read_job(job_id):
    return jsonify(_require(job_id).summary())


@app.get("/api/jobs/<job_id>/mapping")
def read_mapping(job_id):
    job = _require(job_id)
    if job.status != "done":
        abort(409, "job is not finished")

    response = jsonify({"rows": job.mapping, "count": len(job.mapping)})
    # This pairs every real value with its replacement. It is the one object
    # that can undo the redaction, so it is never cached anywhere.
    response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/jobs/<job_id>/download")
def download(job_id):
    job = _require(job_id)
    if job.status != "done" or job.output is None:
        abort(409, "job is not finished")
    return send_file(job.output, as_attachment=True, download_name=job.output.name)


@app.delete("/api/jobs/<job_id>")
def remove_job(job_id):
    if not store.delete(job_id):
        abort(404, "no such job")
    return "", 204


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(409)
@app.errorhandler(413)
def as_json(error):
    message = getattr(error, "description", str(error))
    if error.code == 413:
        message = f"file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)} MB"
    return jsonify({"error": message}), error.code


@app.get("/", defaults={"path": ""})
@app.get("/<path:path>")
def interface(path):
    if not DIST.exists():
        return jsonify({"error": "interface not built; run npm run build in web/"}), 404
    if path and (DIST / path).is_file():
        return send_from_directory(DIST, path)
    return send_from_directory(DIST, "index.html")


def _require(job_id):
    job = store.get(job_id)
    if job is None:
        abort(404, "no such job")
    return job


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), threaded=True)
