"""Background jobs, because a full run takes about a minute.

A synchronous request that long hits browser and proxy timeouts and leaves the
page dead, so uploads start a job and the client polls it.
"""

import shutil
import tempfile
import threading
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from pii_redactor.pipeline import run
from pii_redactor.transforms import build_transform, link_names

# The tiles the interface shows, in order, including the ones this document has
# none of: "SSN 0" tells the reader the type is implemented and simply absent.
CATEGORIES = (
    ("PERSON", "PERSON"),
    ("EMAIL", "EMAIL"),
    ("PHONE", "PHONE"),
    ("COMPANY", "ORGANIZATION"),
    ("ADDRESS", "LOCATION"),
    ("SSN", "SSN"),
    ("CREDIT_CARD", "CREDIT_CARD"),
    ("DOB", "DATE_OF_BIRTH"),
    ("IP_ADDRESS", "IP_ADDRESS"),
)

_LABEL_TO_CATEGORY = {label: category for category, label in CATEGORIES}

JOB_TTL_SECONDS = 3600


@dataclass
class Job:
    id: str
    filename: str
    directory: Path
    status: str = "queued"
    error: str = ""
    output: Path = None
    stats: dict = field(default_factory=dict)
    mapping: list = field(default_factory=list)
    created: float = field(default_factory=time.time)

    def summary(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "filename": self.filename,
            "error": self.error,
            "output_name": self.output.name if self.output else None,
            "stats": self.stats,
        }


class JobStore:
    def __init__(self):
        self._jobs = {}
        self._lock = threading.Lock()
        self._root = Path(tempfile.mkdtemp(prefix="pii-jobs-"))

    def create(self, filename: str, data) -> Job:
        self.prune()
        job_id = uuid.uuid4().hex
        directory = self._root / job_id
        directory.mkdir(parents=True)

        source = directory / filename
        data.save(str(source))

        job = Job(id=job_id, filename=filename, directory=directory)
        with self._lock:
            self._jobs[job_id] = job
        threading.Thread(target=self._work, args=(job, source), daemon=True).start()
        return job

    def get(self, job_id: str):
        with self._lock:
            return self._jobs.get(job_id)

    def delete(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.pop(job_id, None)
        if job is None:
            return False
        shutil.rmtree(job.directory, ignore_errors=True)
        return True

    def prune(self) -> None:
        cutoff = time.time() - JOB_TTL_SECONDS
        with self._lock:
            stale = [job for job in self._jobs.values() if job.created < cutoff]
            for job in stale:
                self._jobs.pop(job.id, None)
        for job in stale:
            shutil.rmtree(job.directory, ignore_errors=True)

    def _work(self, job: Job, source: Path) -> None:
        job.status = "running"
        started = time.perf_counter()
        try:
            destination = job.directory / f"pseudonymized_{job.filename}"
            transform = build_transform("redact", policy="fake")
            link_names(source, transform)
            stats = run(source, destination, transform)

            elapsed = (time.perf_counter() - started) * 1000
            job.output = destination
            job.mapping = _mapping_rows(transform)
            job.stats = _stats(stats.by_label, len(job.mapping), elapsed)
            job.status = "done"
        except Exception as error:  # surfaced to the client rather than swallowed
            job.error = f"{type(error).__name__}: {error}"
            job.status = "error"


def _mapping_rows(transform) -> list:
    mapping = getattr(getattr(transform, "policy", None), "mapping", {})
    rows = [
        {
            "type": _LABEL_TO_CATEGORY.get(label, label),
            "original": original,
            "replacement": replacement,
        }
        for (label, original), replacement in mapping.items()
    ]
    return sorted(rows, key=lambda row: (row["type"], row["original"].lower()))


def _stats(by_label: Counter, unique_mappings: int, elapsed_ms: float) -> dict:
    counts = {
        category: by_label.get(label, 0) for category, label in CATEGORIES
    }
    return {
        "total_entities": sum(counts.values()),
        "unique_mappings": unique_mappings,
        "categories_found": sum(1 for value in counts.values() if value),
        "processing_ms": round(elapsed_ms, 2),
        "categories": counts,
    }
