"""Storage package for S3/Garage-compatible PDF storage.

Exports:
    StorageClient: Low-level S3 client wrapper
    StorageService: High-level PDF storage operations
    provide: Provider function for dependency injection
"""

from app.pkgs.storage.client import StorageClient
from app.pkgs.storage.service import StorageService, provide

__all__ = ["StorageClient", "StorageService", "provide"]
