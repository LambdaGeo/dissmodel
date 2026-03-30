from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, TYPE_CHECKING

if TYPE_CHECKING:
    from dissmodel.core.schemas import ExperimentRecord


class ModelExecutor(ABC):
    """
    Base interface for DisSModel executors.

    Subclasses register themselves automatically in ExecutorRegistry
    via __init_subclass__ — no boilerplate required.

    Minimal implementation
    ----------------------
    class MyExecutor(ModelExecutor):
        name = "my_model"

        def load(self, record: ExperimentRecord):
            return gpd.read_file(record.source.uri)

        def run(self, record: ExperimentRecord):
            data = self.load(record)
            # ... run simulation ...
            return data

        def save(self, result, record: ExperimentRecord) -> ExperimentRecord:
            record.status = "completed"
            return record

    CLI usage
    ---------
    if __name__ == "__main__":
        from dissmodel.cli import run_cli
        run_cli(MyExecutor)
    """

    # Static class attribute — the registry key.
    # Must be a plain string, never a property.
    name: ClassVar[str]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        from .registry import ExecutorRegistry
        if hasattr(cls, "name"):
            ExecutorRegistry.register(cls)

    # ── Required lifecycle methods ────────────────────────────────────────────

    @abstractmethod
    def load(self, record: ExperimentRecord):
        """
        Load and resolve the input dataset.

        Responsibilities:
        - Resolve URI (s3://, http://, local path)
        - Apply column_map (vector) or band_map (raster)
        - Fill record.source.checksum with sha256 of the loaded data
        - Return data in the format expected by run()
        """

    @abstractmethod
    def run(self, record: ExperimentRecord):
        """
        Execute the simulation.

        Receives record with resolved_spec and parameters already merged.
        Returns raw result — format defined by the subclass and
        consumed by save().
        """

    @abstractmethod
    def save(self, result, record: ExperimentRecord) -> ExperimentRecord:
        """
        Persist the result and return the updated record.

        Responsibilities:
        - Save output to destination (local path or s3://)
        - Fill record.output_path and record.output_sha256
        - Set record.status = "completed"
        - Return the complete record
        """

    # ── Optional hook ─────────────────────────────────────────────────────────

    def validate(self, record: ExperimentRecord) -> None:
        """
        Validate spec and data before running.

        Called by runner before run(). Override to check canonical
        columns/bands, value ranges, etc.
        Raise ValueError with an actionable message if invalid.

        Default implementation: no-op.
        """

    # ── Utilities available to subclasses ─────────────────────────────────────

    def _resolve_uri(self, uri: str) -> str:
        """
        Resolve any URI to a local path accessible by the executor.

        s3://bucket/key  → downloads to /tmp/<filename>, returns path
        http(s)://...    → downloads to /tmp/<filename>, returns path
        /local/path      → returns as-is
        """
        import os
        import urllib.request

        if uri.startswith("s3://"):
            from dissmodel.io._storage import get_default_client
            minio          = get_default_client()
            bucket, key    = uri[5:].split("/", 1)
            local_path     = f"/tmp/{os.path.basename(key)}"
            minio.fget_object(bucket, key, local_path)
            return local_path

        if uri.startswith("http://") or uri.startswith("https://"):
            filename   = uri.split("/")[-1].split("?")[0]
            local_path = f"/tmp/{filename}"
            urllib.request.urlretrieve(uri, local_path)
            return local_path

        return uri

    @staticmethod
    def _sha256(path_or_bytes) -> str:
        """Compute sha256 of a file path or bytes."""
        import hashlib
        if isinstance(path_or_bytes, bytes):
            return hashlib.sha256(path_or_bytes).hexdigest()
        with open(path_or_bytes, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
