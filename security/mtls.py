"""
TLS & mTLS Configuration and SSLContext Builder.
Builds Python standard ssl.SSLContext instances for secure MQTT and HTTP communications.
"""

from pathlib import Path
import ssl
from typing import Optional, Tuple

from security.config import SecurityConfig


class MTLSContextBuilder:
    """
    Constructs server and client SSLContext objects with certificate chain validation.
    """

    @staticmethod
    def create_server_context(
        server_cert: Path,
        server_key: Path,
        ca_cert: Optional[Path] = None,
        require_client_cert: bool = False,
    ) -> ssl.SSLContext:
        """
        Build an SSLContext for server-side TLS / mTLS termination.
        """
        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(certfile=str(server_cert), keyfile=str(server_key))

        if require_client_cert and ca_cert and ca_cert.exists():
            ctx.verify_mode = ssl.CERT_REQUIRED
            ctx.load_verify_locations(cafile=str(ca_cert))
        else:
            ctx.verify_mode = ssl.CERT_NONE

        return ctx

    @staticmethod
    def create_client_context(
        ca_cert: Optional[Path] = None,
        client_cert: Optional[Path] = None,
        client_key: Optional[Path] = None,
        check_hostname: bool = True,
    ) -> ssl.SSLContext:
        """
        Build an SSLContext for client-side connection verification and mutual auth presentation.
        """
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

        if ca_cert and ca_cert.exists():
            ctx.load_verify_locations(cafile=str(ca_cert))
            ctx.check_hostname = check_hostname
            ctx.verify_mode = ssl.CERT_REQUIRED
        else:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        if client_cert and client_key and client_cert.exists() and client_key.exists():
            ctx.load_cert_chain(certfile=str(client_cert), keyfile=str(client_key))

        return ctx

    @staticmethod
    def get_configured_contexts(config: SecurityConfig) -> Tuple[Optional[ssl.SSLContext], Optional[ssl.SSLContext]]:
        """
        Return (server_context, client_context) if TLS is enabled, else (None, None).
        """
        if not config.tls_enabled:
            return None, None

        server_ctx = MTLSContextBuilder.create_server_context(
            server_cert=config.server_cert_path,
            server_key=config.server_key_path,
            ca_cert=config.ca_cert_path,
            require_client_cert=config.mtls_enabled,
        )

        client_ctx = MTLSContextBuilder.create_client_context(
            ca_cert=config.ca_cert_path,
            client_cert=config.client_cert_path if config.mtls_enabled else None,
            client_key=config.client_key_path if config.mtls_enabled else None,
            check_hostname=True,
        )

        return server_ctx, client_ctx


