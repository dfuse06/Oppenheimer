"""Resolve the current mainline/stable kernel release straight from kernel.org.

Hardcoding a specific "-rcN" or point release in the UI goes stale the moment
a newer one ships, because kernel.org only keeps the LATEST tarball at a
given URL (an old -rcN or superseded point release 404s). These helpers let
the UI offer "auto" version choices that are always resolved to whatever is
actually current at request time, so no code change is needed to keep up.
"""

from __future__ import annotations

import json
import time
import urllib.request

RELEASES_URL = "https://www.kernel.org/releases.json"

AUTO_MAINLINE = "Latest Mainline (auto)"
AUTO_STABLE = "Latest Stable (auto)"

_AUTO_MONIKERS = {
    AUTO_MAINLINE: "mainline",
    AUTO_STABLE: "stable",
}

_CACHE_TTL_SECONDS = 300.0
_cache: dict[str, tuple[float, str, str]] = {}


def auto_version_labels() -> list[str]:
    """Combo-box labels for the selectable "auto-detect latest" versions."""
    return list(_AUTO_MONIKERS)


def is_auto_version(version: str) -> bool:
    """True if `version` is one of the "auto-detect latest" labels."""
    return version in _AUTO_MONIKERS


def resolve_latest_release(version: str, timeout: float = 10.0) -> tuple[str, str]:
    """Resolve an "auto" label to a concrete (version, tarball_url) pair.

    Results are cached for a few minutes so a single build/download action
    (which may need the version more than once) only hits the network once.
    Raises RuntimeError/ValueError on failure.
    """
    moniker = _AUTO_MONIKERS.get(version)
    if moniker is None:
        raise ValueError(f"Not an auto version label: {version!r}")

    cached = _cache.get(moniker)
    if cached and (time.monotonic() - cached[0]) < _CACHE_TTL_SECONDS:
        return cached[1], cached[2]

    try:
        with urllib.request.urlopen(RELEASES_URL, timeout=timeout) as response:
            data = json.load(response)
    except (OSError, ValueError) as exc:
        raise RuntimeError(
            f"Could not reach kernel.org to resolve the latest {moniker} release: {exc}"
        ) from exc

    releases = data.get("releases", [])

    # For "stable", cross-check against the authoritative top-level
    # `latest_stable` field, since `releases` can list several stable/
    # longterm point releases and their order isn't guaranteed.
    wanted_version = None
    if moniker == "stable":
        wanted_version = str((data.get("latest_stable") or {}).get("version") or "") or None

    for release in releases:
        if release.get("moniker") != moniker:
            continue
        if wanted_version is not None and str(release.get("version")) != wanted_version:
            continue
        resolved_version = str(release["version"])
        resolved_url = str(release["source"])
        _cache[moniker] = (time.monotonic(), resolved_version, resolved_url)
        return resolved_version, resolved_url

    raise RuntimeError(f"kernel.org did not report a current {moniker!r} release.")
