"""Isolated lifecycle prototype; never admits records into production catalogs."""
from .workflow import Workflow, Profile, Response, LifecycleError, digest
__version__ = "0.1.0"
