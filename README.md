# IP / Network Toolbox MVP

This project implements a minimal **IP/Network toolbox** similar to [ip.skk.moe](https://ip.skk.moe).  It is intended as a self‑hostable service that you can deploy on a VPS, container platform or serverless environment.  The MVP (minimum viable product) focuses on core functionality and a straightforward architecture to make it easy to extend and maintain.

## Features

### 1. Local IP Lookup（本机 IP 查询）

* Fetches both **IPv4** and **IPv6** addresses (when available).  If a protocol is unavailable the response clearly indicates this.
* Displays geolocation information: country, region, city, ASN and ISP using two independent data sources.  This redundancy improves accuracy and provides a fallback in case one provider fails.
* Includes a **privacy toggle** on the client that hides your IP and location data without affecting the backend.  No IP or location data is logged by default.
* Runs a simple **connectivity test** against a list of common sites (e.g. Google, GitHub, YouTube, Cloudflare, Taobao, Bilibili).  Round‑trip time (RTT) is measured in the browser using `fetch()` and `performance.now()`.  Timeouts and concurrency limits prevent the UI from blocking.

### 2. IP Intelligence（IP 洞察）

* Accepts an IP address (or leaves it blank to query the current client) and queries multiple third‑party IP data providers in parallel.
* Normalises provider responses into a common schema with fields such as `country`, `region`, `city`, `asn`, `asn_org`, and `isp`.
* Renders a table comparing the results from each provider to highlight discrepancies.
* Implements client‑side caching via `sessionStorage` to respect rate limits.  If a provider fails it is gracefully degraded and marked as unavailable.

### 3. WebRTC Leak Test（STUN／WebRTC 检测）

* Creates an `RTCPeerConnection` with a list of STUN servers and enumerates ICE candidates.
* Parses the candidates to reveal public and private (local) IP addresses that might be exposed by WebRTC.
* Provides a concise explanation of the results and warns when a private IP is exposed.

### Optional Enhancements（增强功能设计）

The code includes design notes for optional features which can be implemented later:

* **Split Tunnel Test** – use multiple probe endpoints to discover the exit IP for different categories of sites when using split‑tunnel VPN or policy‑based routing.  A JSON configuration format for probe definitions is provided.
* **CDN POP Lookup** – demonstrate how to parse CDN response headers (e.g. `cf-ray`, `x-fastly-request-id`) to determine which edge node your request hits.
* **DNS Egress Lookup** – outline approaches for detecting your DNS resolver’s egress IP via OpenDNS or a custom DoH service.

## Architecture Overview

```text
┌───────────────────────────────────────────────────────────────────────────────┐
│                                Client (Browser)                              │
│  - Static HTML/JS served from FastAPI                                        │
│  - Performs WebRTC leak test and connectivity checks using fetch()           │
│  - Calls backend API endpoints via HTTP                                      │
│                                                                              │
├───────────────────────────────────────────────────────────────────────────────┤
│                              Backend (FastAPI)                               │
│  - `/api/local_ip` : get IPv4/IPv6 + geo/ASN from multiple providers         │
│  - `/api/ip_intel` : aggregate IP intelligence across providers              │
│  - `/api/request_meta` : show forwarded/proxy headers                        │
│  - Provides static files under `/`                                           │
│  - Implements timeouts, retries and error handling                           │
│  - No persistent storage; privacy‑friendly (logs can be disabled)            │
│                                                                              │
├───────────────────────────────────────────────────────────────────────────────┤
│                          Third‑party IP Data Providers                       │
│  - ipapi.co, ipinfo.io, ipwho.is, ipdata.co, ip-api.com, etc.                │
│  - Called from the backend via HTTPX with sensible timeouts                  │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Project Structure

```text
ip_network_toolbox_mvp/
├── README.md                 – this file
├── main.py                   – FastAPI application entry point
├── ip_providers.py           – provider definitions & helper functions
├── models.py                 – Pydantic models for request/response schemas
├── config/
│   ├── probes.json           – sample probe definitions for split tunnel test
│   └── sites.json            – list of sites for connectivity tests
├── static/
│   ├── whoami.html           – compact page similar to ip.skk.moe
│   ├── index.html            – Local IP lookup page
│   ├── ip_intel.html         – IP intelligence page
│   ├── webrtc.html           – WebRTC leak test page
│   ├── styles.css            – minimal styling
│   └── scripts/
│       ├── common.js         – shared JS helpers (fetch wrapper, UI)
│       ├── index.js          – behaviour for index.html
│       ├── whoami.js         – behaviour for whoami.html
│       ├── ip_intel.js       – behaviour for ip_intel.html
│       └── webrtc.js         – behaviour for webrtc.html
└── requirements.txt          – Python dependencies
```


## Quick Routes

- `/`：简洁 IP 检测页（类似 ip.skk.moe）
- `/toolbox`：原完整工具页
- `/ip-intel`：指定 IP 多源信息比对
- `/webrtc`：WebRTC 泄露检测

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/ip_network_toolbox_mvp.git
cd ip_network_toolbox_mvp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload  # serve at http://127.0.0.1:8000
```

To build a production Docker image you can create a `Dockerfile` based on `python:3.11-slim`, copy the code, install dependencies and run `uvicorn`.

## Configuration

* `config/probes.json` contains example probe endpoints grouped by category for the split tunnel test.  You can extend it with your own probes (e.g. Cloudflare Workers returning the caller’s IP).
* `config/sites.json` defines the list of domains used for the connectivity test.  Edit this file to customise the test targets.

## Deployment

This application is self‑contained and can run anywhere Python 3.10+ is available.  Below are two typical deployment patterns:

1. **VPS / Bare‑Metal** – Use `gunicorn` or `uvicorn` behind Nginx.  Example systemd service:

   ```ini
   [Unit]
   Description=IP Network Toolbox
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/srv/ip_network_toolbox_mvp
   ExecStart=/srv/ip_network_toolbox_mvp/venv/bin/uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

2. **Serverless / Platform as a Service** – The FastAPI application is stateless, so it runs well on platforms like Vercel, Fly.io or Cloudflare Workers (via [fastapi-aws-lambda](https://github.com/awslabs/aws-lambda-powertools-python/tree/main/examples/fastapi)).  Ensure your platform supports outbound HTTPS connections to the IP data providers.

### Environment Variables

Some IP data providers require API tokens for higher quotas or additional fields.  If you have such tokens you can set them using environment variables:

* `IPINFO_TOKEN` – token for ipinfo.io
* `IPDATA_API_KEY` – token for ipdata.co
* `IPSTACK_API_KEY` – token for ipstack.com

The `ip_providers.py` module reads these values automatically and uses them where appropriate.

## Privacy Statement

This toolbox is designed to be **privacy‑first**:

* The backend does **not** persist IP addresses or geolocation data; it merely processes them in memory and returns the results to the caller.
* Client‑side controls let you hide the display of your IP or location.  This affects only the UI; the backend still needs to query providers to assemble the data.
* Logging is disabled by default.  If you enable logging, consider redacting IP addresses or disabling logs entirely for compliance with privacy laws.

## Further Work

The provided MVP lays the groundwork for more advanced diagnostics.  Future improvements might include:

* A richer UI built with a modern framework such as React or Vue.
* Real split‑tunnel probing using edge functions (e.g. Cloudflare Workers) with dynamic probe discovery.
* CDN POP detection for multiple CDN providers.
* DNS egress detection via custom DoH endpoints or integration with existing resolver services.
* Authentication / rate limiting for multi‑tenant deployments.
