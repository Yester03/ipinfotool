"""Pydantic models defining request and response schemas for the IP Network toolbox.

These models provide type safety and clear documentation for the FastAPI endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class GeoInfo(BaseModel):
    """Geolocation and network information for an IP address."""

    ip: str = Field(..., description="The IP address queried")
    country: Optional[str] = Field(None, description="Country code or name")
    region: Optional[str] = Field(None, description="Region or state name")
    city: Optional[str] = Field(None, description="City name")
    asn: Optional[str] = Field(None, description="Autonomous system number (e.g. AS12345)")
    as_org: Optional[str] = Field(None, alias="as_org", description="Organization associated with the ASN")
    isp: Optional[str] = Field(None, description="Internet service provider or network name")
    latitude: Optional[float] = Field(None, description="Latitude of the IP location")
    longitude: Optional[float] = Field(None, description="Longitude of the IP location")


class ProviderResult(BaseModel):
    """Result returned by a single IP data provider."""

    provider: str = Field(..., description="Name of the data provider (e.g. ipapi, ipinfo)")
    ok: bool = Field(..., description="Whether the provider responded successfully")
    data: Optional[GeoInfo] = Field(None, description="Parsed geolocation/network data if successful")
    error: Optional[str] = Field(None, description="Error message if the provider failed")


class LocalIPResponse(BaseModel):
    """Response for the /api/local_ip endpoint."""

    ipv4: Optional[str] = Field(None, description="Detected IPv4 address")
    ipv6: Optional[str] = Field(None, description="Detected IPv6 address")
    providers: List[ProviderResult] = Field(
        ..., description="List of provider results with geolocation and network information"
    )


class IPIntelRequest(BaseModel):
    """Request payload for the /api/ip_intel endpoint."""

    ip: Optional[str] = Field(None, description="IP address to query; if omitted, query the caller's IP")


class IPIntelResponse(BaseModel):
    """Response for the /api/ip_intel endpoint."""

    ip: str = Field(..., description="The IP address that was resolved (caller if none provided)")
    providers: List[ProviderResult] = Field(
        ..., description="Results from multiple providers with geolocation and network data"
    )
