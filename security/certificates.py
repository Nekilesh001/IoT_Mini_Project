"""
Local X.509 Certificate & CA Management Module.
Generates and verifies self-signed CA, server, and client certificates for local TLS and mTLS testing.
"""

from datetime import datetime, timedelta, timezone
from ipaddress import ip_address
from pathlib import Path
from typing import List, Optional, Tuple, Union

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

from security.models import CertificateInfo


class CertificateManager:
    """
    Local X.509 certificate generation, serialization, and chain validation.
    """

    @staticmethod
    def generate_private_key(key_size: int = 2048) -> rsa.RSAPrivateKey:
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )

    @staticmethod
    def generate_ca(
        common_name: str = "Smart Factory Local Root CA",
        validity_days: int = 365,
    ) -> Tuple[x509.Certificate, rsa.RSAPrivateKey]:
        """Generate a self-signed Root CA certificate and private key."""
        key = CertificateManager.generate_private_key()
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Smart Factory IIoT"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])

        now = datetime.now(timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(days=validity_days))
            .add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_cert_sign=True,
                    crl_sign=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
            .sign(key, hashes.SHA256())
        )
        return cert, key

    @staticmethod
    def generate_signed_cert(
        common_name: str,
        ca_cert: x509.Certificate,
        ca_key: rsa.RSAPrivateKey,
        san_hosts: Optional[List[str]] = None,
        is_server: bool = True,
        validity_days: int = 90,
    ) -> Tuple[x509.Certificate, rsa.RSAPrivateKey]:
        """Generate an end-entity (server or client) certificate signed by the local CA."""
        key = CertificateManager.generate_private_key()
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Smart Factory IIoT"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])

        now = datetime.now(timezone.utc)
        builder = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(ca_cert.subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5))
            .not_valid_after(now + timedelta(days=validity_days))
            .add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )
            .add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            )
        )

        # Extended key usages (Server Auth or Client Auth)
        if is_server:
            builder = builder.add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]),
                critical=False,
            )
        else:
            builder = builder.add_extension(
                x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]),
                critical=False,
            )

        # Subject Alternative Names (SAN)
        san_entries: List[x509.GeneralName] = []
        hosts = san_hosts or [common_name, "localhost", "127.0.0.1"]
        for h in hosts:
            try:
                ip_obj = ip_address(h)
                san_entries.append(x509.IPAddress(ip_obj))
            except ValueError:
                san_entries.append(x509.DNSName(h))

        if san_entries:
            builder = builder.add_extension(
                x509.SubjectAlternativeName(san_entries),
                critical=False,
            )

        cert = builder.sign(ca_key, hashes.SHA256())
        return cert, key

    @staticmethod
    def save_cert_and_key(
        cert: x509.Certificate,
        key: rsa.RSAPrivateKey,
        cert_path: Union[str, Path],
        key_path: Union[str, Path],
    ) -> None:
        """Serialize certificate and private key to disk in PEM format."""
        cert_p = Path(cert_path)
        key_p = Path(key_path)
        cert_p.parent.mkdir(parents=True, exist_ok=True)
        key_p.parent.mkdir(parents=True, exist_ok=True)

        with open(cert_p, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(key_p, "wb") as f:
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

    @staticmethod
    def load_cert_from_bytes(data: bytes) -> x509.Certificate:
        return x509.load_pem_x509_certificate(data)

    @staticmethod
    def inspect_certificate(cert: x509.Certificate) -> CertificateInfo:
        """Extract metadata and expiration details from an X.509 certificate."""
        now = datetime.now(timezone.utc)
        not_before = cert.not_valid_before_utc
        not_after = cert.not_valid_after_utc

        # Extract Common Names
        subject_cn = cert.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value
        issuer_cn = cert.issuer.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value

        # Extract SANs
        san_list = []
        try:
            san_ext = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            for san in san_ext.value:
                san_list.append(str(san.value))
        except x509.ExtensionNotFound:
            pass

        # Check CA
        is_ca = False
        try:
            bc_ext = cert.extensions.get_extension_for_oid(x509.ExtensionOID.BASIC_CONSTRAINTS)
            is_ca = bc_ext.value.ca
        except x509.ExtensionNotFound:
            pass

        is_expired = now > not_after or now < not_before
        days_remaining = (not_after - now).days

        return CertificateInfo(
            subject_cn=str(subject_cn),
            issuer_cn=str(issuer_cn),
            serial_number=str(cert.serial_number),
            not_before=not_before,
            not_after=not_after,
            san_entries=san_list,
            is_ca=is_ca,
            is_expired=is_expired,
            days_until_expiration=max(0, days_remaining),
        )

    @staticmethod
    def verify_cert_chain(cert: x509.Certificate, ca_cert: x509.Certificate) -> bool:
        """Verify that cert was signed by ca_cert public key."""
        try:
            from cryptography.hazmat.primitives.asymmetric import padding
            ca_public_key = ca_cert.public_key()
            ca_public_key.verify(
                cert.signature,
                cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                cert.signature_hash_algorithm,
            )
            return True
        except Exception:
            return False

    @staticmethod
    def verify_hostname_san(cert: x509.Certificate, hostname: str) -> bool:
        """Verify hostname matches subject CN or SAN entry."""
        info = CertificateManager.inspect_certificate(cert)
        if hostname == info.subject_cn:
            return True
        return hostname in info.san_entries
