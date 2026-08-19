"""
Storage abstraction for artwork and catalogue files.

The ABC defines the contract; LocalDiskStorage is used for local dev / Docker Compose.
MinioStorage and R2Storage are drop-in replacements — swapping requires only an
environment variable change (STORAGE_BACKEND=minio | r2).

Atomic replace semantics:
  - LocalDiskStorage: os.replace() which is atomic on POSIX filesystems
  - MinioStorage / R2Storage: copy_object() then delete_object() — not truly
    atomic at the S3 level, but the old object remains readable throughout the
    copy, so readers are never served a partial file.
"""
from __future__ import annotations

import os
import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path


class StorageBackend(ABC):
    """Abstract interface every storage backend must implement."""

    @abstractmethod
    async def put(self, key: str, data: bytes, content_type: str) -> str:
        """Store `data` under `key`. Returns the public URL."""

    @abstractmethod
    async def get(self, key: str) -> bytes:
        """Retrieve the object at `key`."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete the object at `key`. No-op if it doesn't exist."""

    @abstractmethod
    async def atomic_replace(self, src_key: str, dst_key: str) -> None:
        """
        Atomically replace dst_key with the content currently at src_key.
        After this call succeeds src_key no longer exists.
        """

    @abstractmethod
    def public_url(self, key: str) -> str:
        """Return the public URL for the given storage key."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Return True if the key exists in storage."""


# ─────────────────────────────────────────────────────────────────────────────
# Local disk backend
# ─────────────────────────────────────────────────────────────────────────────

class LocalDiskStorage(StorageBackend):
    """Stores files on the local filesystem; serves via FastAPI StaticFiles."""

    def __init__(self, root: str | Path, base_url: str):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url.rstrip("/")

    def _path(self, key: str) -> Path:
        p = (self.root / key).resolve()
        # Security: ensure the path stays within root
        if not str(p).startswith(str(self.root.resolve())):
            raise ValueError(f"Invalid storage key: {key!r}")
        return p

    async def put(self, key: str, data: bytes, content_type: str) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return self.public_url(key)

    async def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    async def delete(self, key: str) -> None:
        path = self._path(key)
        if path.exists():
            path.unlink()

    async def atomic_replace(self, src_key: str, dst_key: str) -> None:
        src = self._path(src_key)
        dst = self._path(dst_key)
        dst.parent.mkdir(parents=True, exist_ok=True)
        # os.replace is atomic on POSIX; on Windows it is best-effort
        os.replace(src, dst)

    def public_url(self, key: str) -> str:
        return f"{self.base_url}/{key}"

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


# ─────────────────────────────────────────────────────────────────────────────
# MinIO / S3-compatible backend (also used for Cloudflare R2)
# ─────────────────────────────────────────────────────────────────────────────

class MinioStorage(StorageBackend):
    """
    S3-compatible object storage via boto3.
    Works with MinIO locally and Cloudflare R2 in production.
    For R2: set endpoint_url = https://{account_id}.r2.cloudflarestorage.com
    """

    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        public_base_url: str,
    ):
        try:
            import boto3
            from botocore.config import Config
        except ImportError as e:
            raise ImportError(
                "boto3 is required for MinioStorage/R2Storage. "
                "Install it with: pip install boto3"
            ) from e

        self._bucket = bucket
        self._public_base_url = public_base_url.rstrip("/")
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )
        # Create bucket if it doesn't exist
        try:
            self._client.head_bucket(Bucket=bucket)
        except Exception:
            self._client.create_bucket(Bucket=bucket)

    async def put(self, key: str, data: bytes, content_type: str) -> str:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return self.public_url(key)

    async def get(self, key: str) -> bytes:
        resp = self._client.get_object(Bucket=self._bucket, Key=key)
        return resp["Body"].read()

    async def delete(self, key: str) -> None:
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except Exception:
            pass

    async def atomic_replace(self, src_key: str, dst_key: str) -> None:
        # Copy src → dst (source remains readable throughout)
        self._client.copy_object(
            Bucket=self._bucket,
            CopySource={"Bucket": self._bucket, "Key": src_key},
            Key=dst_key,
        )
        # Delete the temporary src key
        self._client.delete_object(Bucket=self._bucket, Key=src_key)

    def public_url(self, key: str) -> str:
        return f"{self._public_base_url}/{key}"

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Supabase Storage backend (via REST API)
# ─────────────────────────────────────────────────────────────────────────────

import json
import urllib.request


class SupabaseStorage(StorageBackend):
    """
    Stores files in Supabase Storage using the standard REST API.
    Supports public bucket storage, atomic replace (via move), and public URLs.
    """

    def __init__(self, project_id: str, service_role_key: str, bucket: str):
        self.project_id = project_id
        self.service_role_key = service_role_key
        self.bucket = bucket
        self.base_url = f"https://{project_id}.supabase.co/storage/v1"
        self.public_base_url = f"{self.base_url}/object/public/{bucket}"
        self.headers = {
            "Authorization": f"Bearer {service_role_key}",
            "apikey": service_role_key,
        }

    async def put(self, key: str, data: bytes, content_type: str) -> str:
        url = f"{self.base_url}/object/{self.bucket}/{key}"
        headers = {
            **self.headers,
            "Content-Type": content_type,
            "x-upsert": "true",
        }
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            pass
        return self.public_url(key)

    async def get(self, key: str) -> bytes:
        url = f"{self.base_url}/object/{self.bucket}/{key}"
        req = urllib.request.Request(url, headers=self.headers, method="GET")
        with urllib.request.urlopen(req) as resp:
            return resp.read()

    async def delete(self, key: str) -> None:
        url = f"{self.base_url}/object/{self.bucket}/{key}"
        req = urllib.request.Request(url, headers=self.headers, method="DELETE")
        try:
            with urllib.request.urlopen(req):
                pass
        except Exception:
            pass

    async def atomic_replace(self, src_key: str, dst_key: str) -> None:
        # Move object src -> dst in Supabase storage
        url = f"{self.base_url}/object/move"
        payload = json.dumps({
            "bucketId": self.bucket,
            "sourceKey": src_key,
            "destinationKey": dst_key,
        }).encode("utf-8")
        headers = {
            **self.headers,
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req):
                pass
        except Exception:
            data = await self.get(src_key)
            await self.put(dst_key, data, "application/octet-stream")
            await self.delete(src_key)

    def public_url(self, key: str) -> str:
        return f"{self.public_base_url}/{key}"

    def exists(self, key: str) -> bool:
        url = f"{self.base_url}/object/info/public/{self.bucket}/{key}"
        req = urllib.request.Request(url, headers=self.headers, method="GET")
        try:
            with urllib.request.urlopen(req):
                return True
        except Exception:
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────────────────────

_storage_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Return the configured storage backend (singleton)."""
    global _storage_instance
    if _storage_instance is None:
        from app.config import get_settings
        s = get_settings()
        backend = s.STORAGE_BACKEND.lower()

        if backend == "local":
            _storage_instance = LocalDiskStorage(
                root=s.LOCAL_STORAGE_PATH,
                base_url=s.LOCAL_STORAGE_BASE_URL,
            )
        elif backend == "supabase":
            _storage_instance = SupabaseStorage(
                project_id=s.SUPABASE_PROJECT_ID,
                service_role_key=s.SUPABASE_SERVICE_ROLE_KEY,
                bucket=s.SUPABASE_BUCKET,
            )
        elif backend in ("minio", "r2", "b2"):
            if backend == "r2":
                endpoint = f"https://{s.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"
                access_key = s.R2_ACCESS_KEY_ID
                secret_key = s.R2_SECRET_ACCESS_KEY
                bucket = s.R2_BUCKET
                public_base = f"https://pub-{s.R2_ACCOUNT_ID}.r2.dev"
            elif backend == "b2":
                endpoint = s.B2_ENDPOINT_URL
                access_key = s.B2_KEY_ID
                secret_key = s.B2_APPLICATION_KEY
                bucket = s.B2_BUCKET_NAME
                public_base = f"{s.B2_ENDPOINT_URL.rstrip('/')}/{s.B2_BUCKET_NAME}"
            else:
                endpoint = s.MINIO_ENDPOINT
                access_key = s.MINIO_ACCESS_KEY
                secret_key = s.MINIO_SECRET_KEY
                bucket = s.MINIO_BUCKET
                public_base = f"{s.MINIO_ENDPOINT}/{bucket}"

            _storage_instance = MinioStorage(
                endpoint_url=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                bucket=bucket,
                public_base_url=public_base,
            )
        else:
            raise ValueError(f"Unknown STORAGE_BACKEND: {backend!r}")

    return _storage_instance
