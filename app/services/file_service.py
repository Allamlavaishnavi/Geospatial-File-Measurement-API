import os
import shutil
import uuid
import datetime
from typing import Dict, Optional, Tuple
from app.models.schemas import FileSummaryResponse, FileMeasurementsResponse, FileStatusEnum


class FileService:
    def __init__(self, upload_dir: str = "uploads"):
        self.upload_dir = os.path.abspath(upload_dir)
        os.makedirs(self.upload_dir, exist_ok=True)
        # Thread-safe in-memory store
        self._summaries: Dict[str, FileSummaryResponse] = {}
        self._measurements: Dict[str, FileMeasurementsResponse] = {}

    def generate_id(self) -> str:
        """Generates a clean unique 8-character string ID."""
        return uuid.uuid4().hex[:8]

    def create_upload_dir(self, file_id: str) -> str:
        """Creates an isolated directory for the given file ID."""
        file_dir = os.path.join(self.upload_dir, file_id)
        os.makedirs(file_dir, exist_ok=True)
        return file_dir

    def save_file_content(self, file_id: str, filename: str, content: bytes) -> str:
        """Saves uploaded binary content into the file's isolated directory."""
        file_dir = self.create_upload_dir(file_id)
        target_path = os.path.join(file_dir, filename)
        with open(target_path, "wb") as f:
            f.write(content)
        return target_path

    def get_file_dir(self, file_id: str) -> str:
        return os.path.join(self.upload_dir, file_id)

    def store_file_record(
        self,
        file_id: str,
        summary: FileSummaryResponse,
        measurements: FileMeasurementsResponse
    ) -> None:
        """Stores the processed file summary and measurement results in memory."""
        self._summaries[file_id] = summary
        self._measurements[file_id] = measurements

    def get_summary(self, file_id: str) -> Optional[FileSummaryResponse]:
        """Retrieves summary by file ID."""
        return self._summaries.get(file_id)

    def get_measurements(self, file_id: str) -> Optional[FileMeasurementsResponse]:
        """Retrieves measurement results by file ID."""
        return self._measurements.get(file_id)

    def cleanup(self, file_id: str) -> None:
        """Clean up filesystem artifacts for a file ID if needed."""
        file_dir = self.get_file_dir(file_id)
        if os.path.exists(file_dir):
            shutil.rmtree(file_dir, ignore_errors=True)
