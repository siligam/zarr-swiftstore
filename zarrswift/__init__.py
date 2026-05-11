from .storage import SwiftStore
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("zarr-swiftstore")
except PackageNotFoundError:
    __version__ = "unknown"
