from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("wooz")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"
