"""
ip_providers.py

This module defines helper functions for querying multiple IP data providers.  Each provider
returns basic geolocation and network information for a given IP address.  The functions
return `ProviderResult` models that encapsulate success/failure status and parsed data.

When adding providers, follow this pattern:
1. Use httpx to make an HTTP GET request with a sensible timeout (3–5 seconds).
2. Catch exceptions and return a ProviderResult with ok=False and an error message.
3. Normalise the response fields into the `GeoInfo` model.

If an API key or token is required, fetch it from the corresponding environment variable
to avoid hard‑coding secrets.  See README.md for supported variables.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx
from .models import GeoInfo, ProviderResult


async def fetch_ipapi(ip: Optional[str] = None) -> ProviderResult:
    """Query ipapi.co for geolocation data.

    ipapi.co has a generous free tier and does not require an API key for basic data.
    """
    base_url = "https://ipapi.co"
    provider_name = "ipapi"
    url = f"{base_url}/{ip or ''}/json/"
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            geo = GeoInfo(
                ip=data.get("ip"),
                country=data.get("country_code") or data.get("country_name"),
                region=data.get("region"),
                city=data.get("city"),
                asn=data.get("asn"),
                as_org=data.get("org"),
                isp=data.get("org"),  # ipapi combines org and ISP
                latitude=float(data.get("latitude")) if data.get("latitude") else None,
                longitude=float(data.get("longitude")) if data.get("longitude") else None,
            )
            return ProviderResult(provider=provider_name, ok=True, data=geo)
        except Exception as exc:
            return ProviderResult(provider=provider_name, ok=False, error=str(exc))


async def fetch_ipinfo(ip: Optional[str] = None) -> ProviderResult:
    """Query ipinfo.io for geolocation data.

    Requires an API token for higher rate limits.  If `IPINFO_TOKEN` is not
    provided in the environment, the free tier is used.
    """
    base_url = "https://ipinfo.io"
    provider_name = "ipinfo"
    token = os.getenv("IPINFO_TOKEN")
    url = f"{base_url}/{ip or ''}/json"
    params = {"token": token} if token else None
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            loc = data.get("loc") or ""
            lat, lon = None, None
            if loc and "," in loc:
                lat_str, lon_str = loc.split(",", 1)
                try:
                    lat, lon = float(lat_str), float(lon_str)
                except ValueError:
                    lat, lon = None, None
            geo = GeoInfo(
                ip=data.get("ip"),
                country=data.get("country"),
                region=data.get("region"),
                city=data.get("city"),
                asn=data.get("org").split(" ")[0] if data.get("org") else None,
                as_org=" ".join(data.get("org").split(" ")[1:]) if data.get("org") else None,
                isp=data.get("org"),
                latitude=lat,
                longitude=lon,
            )
            return ProviderResult(provider=provider_name, ok=True, data=geo)
        except Exception as exc:
            return ProviderResult(provider=provider_name, ok=False, error=str(exc))


async def fetch_ipwhois(ip: Optional[str] = None) -> ProviderResult:
    """Query ipwho.is for geolocation data.

    This provider has no API key and responds with a simple JSON structure.
    """
    base_url = "https://ipwho.is"
    provider_name = "ipwhois"
    url = f"{base_url}/{ip or ''}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success", True):
                raise Exception(data.get("message", "Unknown error"))
            geo = GeoInfo(
                ip=data.get("ip"),
                country=data.get("country_code") or data.get("country"),
                region=data.get("region"),
                city=data.get("city"),
                asn=data.get("asn"),
                as_org=data.get("org"),
                isp=data.get("isp"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
            )
            return ProviderResult(provider=provider_name, ok=True, data=geo)
        except Exception as exc:
            return ProviderResult(provider=provider_name, ok=False, error=str(exc))


async def fetch_ipapi_com(ip: Optional[str] = None) -> ProviderResult:
    """Query ip-api.com for geolocation data.

    ip-api.com provides a free tier with limited fields but no API key required.  It
    returns 429 status if rate limited.  Note: ip-api.com does not support HTTPS on
    the free tier for all endpoints, so we use the JSON endpoint over HTTP.
    """
    provider_name = "ip-api"
    url = f"http://ip-api.com/json/{ip or ''}"
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "success":
                raise Exception(data.get("message", "Unknown error"))
            geo = GeoInfo(
                ip=data.get("query"),
                country=data.get("countryCode") or data.get("country"),
                region=data.get("regionName"),
                city=data.get("city"),
                asn=data.get("as").split(" ")[0] if data.get("as") else None,
                as_org=" ".join(data.get("as").split(" ")[1:]) if data.get("as") else None,
                isp=data.get("isp"),
                latitude=data.get("lat"),
                longitude=data.get("lon"),
            )
            return ProviderResult(provider=provider_name, ok=True, data=geo)
        except Exception as exc:
            return ProviderResult(provider=provider_name, ok=False, error=str(exc))


async def fetch_ipdata(ip: Optional[str] = None) -> ProviderResult:
    """Query ipdata.co for geolocation data.

    ipdata.co requires an API key for most functionality.  Without a key the
    service will respond with an error.  Set the `IPDATA_API_KEY` environment
    variable to enable this provider.  This function will skip the provider if no key
    is present.
    """
    provider_name = "ipdata"
    api_key = os.getenv("IPDATA_API_KEY")
    if not api_key:
        return ProviderResult(provider=provider_name, ok=False, error="No API key configured")
    url = f"https://api.ipdata.co/{ip or ''}"
    params = {"api-key": api_key}
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            geo = GeoInfo(
                ip=data.get("ip"),
                country=data.get("country_code") or data.get("country_name"),
                region=data.get("region") or data.get("region_name"),
                city=data.get("city"),
                asn=data.get("asn"),
                as_org=data.get("organisation"),
                isp=data.get("organisation"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
            )
            return ProviderResult(provider=provider_name, ok=True, data=geo)
        except Exception as exc:
            return ProviderResult(provider=provider_name, ok=False, error=str(exc))


async def fetch_providers(ip: Optional[str] = None) -> list[ProviderResult]:
    """Collect data from all configured providers concurrently.

    Returns a list of ProviderResult objects.  Providers that fail or are not
    configured will return `ok=False` with an error message.
    """
    # Compose the coroutines for providers that should run.  Skip providers
    # requiring keys if the key is not present.
    tasks = [
        fetch_ipapi(ip),
        fetch_ipinfo(ip),
        fetch_ipwhois(ip),
        fetch_ipapi_com(ip),
    ]
    # Add ipdata provider only if key is set
    if os.getenv("IPDATA_API_KEY"):
        tasks.append(fetch_ipdata(ip))
    results = await httpx.AsyncClient().gather(*tasks, return_exceptions=False)  # type: ignore[attr-defined]
    # httpx.AsyncClient.gather isn't available; fallback to asyncio.gather
    import asyncio
    results = await asyncio.gather(*tasks, return_exceptions=True)  # type: ignore
    normalized: list[ProviderResult] = []
    for res in results:
        if isinstance(res, ProviderResult):
            normalized.append(res)
        else:
            # Unexpected exceptions are recorded as generic errors
            normalized.append(ProviderResult(provider="unknown", ok=False, error=str(res)))
    return normalized
