"""
Unit tests for X.509 CertificateManager: CA generation, SAN validation, cert verification, and mTLS context.
"""

import tempfile
from pathlib import Path
import pytest
from security.certificates import CertificateManager
from security.mtls import MTLSContextBuilder


def test_generate_and_verify_certificates():
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. Generate Root CA
        ca_cert, ca_key = CertificateManager.generate_ca(common_name="Smart Factory Local Root CA")
        assert ca_cert is not None
        assert ca_key is not None

        # 2. Generate Server Cert
        server_cert, server_key = CertificateManager.generate_signed_cert(
            common_name="localhost",
            ca_cert=ca_cert,
            ca_key=ca_key,
            san_hosts=["localhost", "127.0.0.1", "factory.local"],
            is_server=True,
        )
        assert server_cert is not None
        assert server_key is not None

        # 3. Verify Certificate Chain
        valid = CertificateManager.verify_cert_chain(server_cert, ca_cert)
        assert valid is True

        # 4. Verify SANs
        valid_san = CertificateManager.verify_hostname_san(server_cert, "factory.local")
        assert valid_san is True

        invalid_san = CertificateManager.verify_hostname_san(server_cert, "attacker.evil.com")
        assert invalid_san is False


def test_client_certificate_and_mtls_context():
    with tempfile.TemporaryDirectory() as tmpdir:
        ca_cert, ca_key = CertificateManager.generate_ca()
        server_cert, server_key = CertificateManager.generate_signed_cert(
            common_name="localhost", ca_cert=ca_cert, ca_key=ca_key, is_server=True
        )
        client_cert, client_key = CertificateManager.generate_signed_cert(
            common_name="edge_agent_01", ca_cert=ca_cert, ca_key=ca_key, is_server=False
        )

        ca_path = Path(tmpdir) / "ca.crt"
        ca_kpath = Path(tmpdir) / "ca.key"
        srv_path = Path(tmpdir) / "server.crt"
        srv_kpath = Path(tmpdir) / "server.key"
        cli_path = Path(tmpdir) / "client.crt"
        cli_kpath = Path(tmpdir) / "client.key"

        CertificateManager.save_cert_and_key(ca_cert, ca_key, ca_path, ca_kpath)
        CertificateManager.save_cert_and_key(server_cert, server_key, srv_path, srv_kpath)
        CertificateManager.save_cert_and_key(client_cert, client_key, cli_path, cli_kpath)

        # Create Server SSLContext
        srv_ctx = MTLSContextBuilder.create_server_context(
            server_cert=srv_path,
            server_key=srv_kpath,
            ca_cert=ca_path,
            require_client_cert=True,
        )
        assert srv_ctx is not None

        # Create Client SSLContext
        cli_ctx = MTLSContextBuilder.create_client_context(
            ca_cert=ca_path,
            client_cert=cli_path,
            client_key=cli_kpath,
            check_hostname=False,
        )
        assert cli_ctx is not None
