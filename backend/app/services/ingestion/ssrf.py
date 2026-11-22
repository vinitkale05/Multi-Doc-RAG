import ipaddress
import socket
import urllib.parse
import httpx
from app.core.errors import AppError


class SSRFValidationError(AppError):
    def __init__(self, detail: str):
        super().__init__(status_code=400, detail=detail, code="SSRF_PROTECTION_TRIGGERED")


def is_ip_allowed(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
        # Block private, loopback, link-local (169.254.x.x cloud metadata), reserved, multicast
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False
        return True
    except ValueError:
        return False


def validate_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFValidationError("Only HTTP and HTTPS protocols are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("Invalid URL: missing hostname.")

    # Disallow known localhost aliases
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "metadata.google.internal", "169.254.169.254"):
        raise SSRFValidationError("Access to localhost or cloud metadata services is forbidden.")

    try:
        # Resolve all DNS A and AAAA records
        addr_info = socket.getaddrinfo(hostname, None)
        for entry in addr_info:
            ip_str = entry[4][0]
            if not is_ip_allowed(ip_str):
                raise SSRFValidationError(f"Target host resolves to restricted IP: {ip_str}")
    except socket.gaierror:
        raise SSRFValidationError(f"Could not resolve host: {hostname}")

    return url


async def fetch_url_safely(url: str, max_bytes: int = 25 * 1024 * 1024) -> tuple[bytes, str]:
    """Safely fetch web page content with SSRF checks, timeout, and max size limits."""
    validated_url = validate_url(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/pdf;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, verify=False) as client:
            response = await client.get(validated_url, headers=headers)
            if response.status_code >= 400:
                raise SSRFValidationError(f"URL returned HTTP status {response.status_code}")

            content = response.content
            if len(content) > max_bytes:
                raise SSRFValidationError(f"Page size exceeds maximum allowed size ({max_bytes} bytes)")

            content_type = response.headers.get("content-type", "").lower()
            if not content_type:
                if validated_url.lower().endswith(".pdf"):
                    content_type = "application/pdf"
                else:
                    content_type = "text/html"
            return content, content_type
    except httpx.TimeoutException:
        raise SSRFValidationError("Connection to URL timed out after 20 seconds.")
    except httpx.RequestError as e:
        raise SSRFValidationError(f"Network error while fetching URL: {str(e)}")
