"""
Entry point for the IP Network Toolbox application.

This file defines the FastAPI application, sets up static file serving, configures
CORS, and exposes API endpoints for local IP lookup and IP intelligence.  The
application uses asynchronous HTTP requests to query multiple IP data providers
in parallel and returns normalised responses.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from models import LocalIPResponse, IPIntelResponse, IPIntelRequest, ProviderResult, RequestMetaResponse
from ip_providers import fetch_providers


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="IP Network Toolbox MVP", docs_url="/docs", redoc_url="/redoc")

# CORS configuration – adjust `allow_origins` to suit your deployment needs.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # in production restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files.  This serves files under /static and also root HTML pages.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    """Serve a compact IP diagnostics page similar to ip.skk.moe."""
    index_path = STATIC_DIR / "whoami.html"
    return FileResponse(index_path)


@app.get("/toolbox", include_in_schema=False)
async def toolbox_page() -> FileResponse:
    """Serve the original toolbox landing page."""
    index_path = STATIC_DIR / "index.html"
    return FileResponse(index_path)


@app.get("/ip-intel", include_in_schema=False)
async def ip_intel_page() -> FileResponse:
    """Serve the IP Intelligence page."""
    page_path = STATIC_DIR / "ip_intel.html"
    return FileResponse(page_path)


@app.get("/webrtc", include_in_schema=False)
async def webrtc_page() -> FileResponse:
    """Serve the WebRTC leak test page."""
    page_path = STATIC_DIR / "webrtc.html"
    return FileResponse(page_path)


async def get_public_ipv4() -> Optional[str]:
    """Resolve the caller's IPv4 address using api.ipify.org."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://api.ipify.org", params={"format": "json"})
            resp.raise_for_status()
            data = resp.json()
            return data.get("ip")
    except Exception:
        return None


async def get_public_ipv6() -> Optional[str]:
    """Resolve the caller's IPv6 address using api64.ipify.org."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://api64.ipify.org", params={"format": "json"})
            resp.raise_for_status()
            data = resp.json()
            return data.get("ip")
    except Exception:
        return None


@app.get("/api/local_ip", response_model=LocalIPResponse)
async def local_ip_endpoint() -> LocalIPResponse:
    """Endpoint for obtaining local IP information and geolocation from multiple providers."""
    ipv4, ipv6 = await asyncio.gather(get_public_ipv4(), get_public_ipv6())
    providers: list[ProviderResult] = await fetch_providers()
    return LocalIPResponse(ipv4=ipv4, ipv6=ipv6, providers=providers)


@app.post("/api/ip_intel", response_model=IPIntelResponse)
async def ip_intel_endpoint(payload: IPIntelRequest) -> IPIntelResponse:
    """Endpoint for IP intelligence.  Accepts an optional IP address in the request body."""
    ip = payload.ip
    # If IP is not provided, attempt to infer via ipify (IPv4) first; fallback to providers.
    if not ip:
        ip = await get_public_ipv4() or await get_public_ipv6() or ""
    providers: list[ProviderResult] = await fetch_providers(ip)
    return IPIntelResponse(ip=ip or "", providers=providers)


@app.get("/api/ip_intel")
async def ip_intel_endpoint_get(ip: Optional[str] = None) -> IPIntelResponse:
    """GET variant of IP intelligence endpoint for convenience in browser queries."""
    return await ip_intel_endpoint(IPIntelRequest(ip=ip))


@app.get("/api/request_meta", response_model=RequestMetaResponse)
async def request_meta_endpoint(request: Request) -> RequestMetaResponse:
    """Expose request metadata useful for debugging proxy/CDN deployments."""
    headers_of_interest = [
        "x-forwarded-for",
        "x-real-ip",
        "cf-connecting-ip",
        "cf-ipcountry",
        "x-forwarded-proto",
        "via",
        "user-agent",
    ]
    header_map = {k: request.headers.get(k) for k in headers_of_interest if request.headers.get(k)}
    return RequestMetaResponse(
        client_ip=request.client.host if request.client else None,
        headers=header_map,
    )


# 404 handler for unknown routes – helps debugging when static pages are missing
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": "Not Found"})
