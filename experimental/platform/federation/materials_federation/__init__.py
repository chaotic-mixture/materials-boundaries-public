"""Additive provider federation; never writes production catalogs."""
from .models import Candidate, Query, SearchPage
from .providers import MaterialsProjectAdapter, NomadAdapter

__all__ = ["Candidate", "Query", "SearchPage", "MaterialsProjectAdapter", "NomadAdapter"]
