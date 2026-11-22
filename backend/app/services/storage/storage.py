import os
import shutil
from abc import ABC, abstractmethod
from typing import BinaryIO
from app.core.config import settings


class BaseStorageService(ABC):
    @abstractmethod
    async def upload(self, file_obj: BinaryIO, filename: str, content_type: str) -> str:
        """Upload a file and return the storage URI."""
        pass

    @abstractmethod
    async def download(self, storage_uri: str) -> bytes:
        """Download file bytes given storage URI."""
        pass

    @abstractmethod
    async def delete(self, storage_uri: str) -> bool:
        """Delete file from storage."""
        pass

    @abstractmethod
    def get_download_url(self, storage_uri: str) -> str:
        """Get accessible download URL for original file."""
        pass


class LocalStorageService(BaseStorageService):
    def __init__(self, base_dir: str = settings.LOCAL_STORAGE_DIR):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)

    async def upload(self, file_obj: BinaryIO, filename: str, content_type: str) -> str:
        target_path = os.path.join(self.base_dir, filename)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "wb") as f:
            shutil.copyfileobj(file_obj, f)
        return f"file://{target_path}"

    async def download(self, storage_uri: str) -> bytes:
        path = storage_uri.replace("file://", "")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Storage path {path} not found")
        with open(path, "rb") as f:
            return f.read()

    async def delete(self, storage_uri: str) -> bool:
        path = storage_uri.replace("file://", "")
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def get_download_url(self, storage_uri: str) -> str:
        return storage_uri


def get_storage_service() -> BaseStorageService:
    return LocalStorageService()
