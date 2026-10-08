"""Federation boundary for a future API; partial failure stays explicit."""
from typing import Literal, Sequence
from .models import Model, Provider, Query, SearchPage
from .providers import AuthenticationRequired, ProviderError

class ProviderFailure(Model):
    provider: str
    kind: Literal["authentication_required", "provider_error"]
    message: str

class FederatedResult(Model):
    query: Query
    pages: tuple[SearchPage, ...]
    failures: tuple[ProviderFailure, ...]
    status: Literal["success", "partial", "failed"]
    quota_credit: Literal[0] = 0


def federated_search(providers: Sequence[Provider], query: Query) -> FederatedResult:
    """One bounded request per configured provider. Never collapse cross-provider identities."""
    if not providers or len({p.provider for p in providers}) != len(providers):
        raise ValueError("Specify at least one provider, without duplicate provider names")
    pages, failures = [], []
    for provider in providers:
        try:
            pages.append(provider.search(query))
        except AuthenticationRequired:
            failures.append(ProviderFailure(provider=provider.provider,
                kind="authentication_required", message="A separately authorized client is required."))
        except ProviderError:
            failures.append(ProviderFailure(provider=provider.provider,
                kind="provider_error", message="Query failed; no result from this provider is assumed."))
    return FederatedResult(query=query, pages=tuple(pages), failures=tuple(failures),
        status="partial" if pages and failures else "success" if pages else "failed")
