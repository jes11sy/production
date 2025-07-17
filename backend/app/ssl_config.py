"""
Конфигурация SSL/HTTPS для development окружения
"""
import os
import ssl
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime
import logging

logger = logging.getLogger(__name__)

def create_self_signed_cert(cert_dir: str = "ssl") -> tuple[str, str]:
    """
    Создание самоподписанного сертификата для development
    
    Args:
        cert_dir: Директория для сохранения сертификатов
        
    Returns:
        Кортеж (путь к сертификату, путь к ключу)
    """
    cert_path = Path(cert_dir)
    cert_path.mkdir(exist_ok=True)
    
    cert_file = cert_path / "cert.pem"
    key_file = cert_path / "key.pem"
    
    # Если сертификат уже существует, возвращаем его
    if cert_file.exists() and key_file.exists():
        logger.info(f"Используется существующий SSL сертификат: {cert_file}")
        return str(cert_file), str(key_file)
    
    # Генерируем приватный ключ
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Создаем сертификат
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "RU"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Moscow"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Moscow"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Request Management System"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("127.0.0.1"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # Сохраняем сертификат
    with open(cert_file, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    # Сохраняем приватный ключ
    with open(key_file, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    logger.info(f"Создан новый SSL сертификат: {cert_file}")
    return str(cert_file), str(key_file)

def get_ssl_context(cert_file: str, key_file: str) -> ssl.SSLContext:
    """
    Создание SSL контекста для uvicorn
    
    Args:
        cert_file: Путь к файлу сертификата
        key_file: Путь к файлу ключа
        
    Returns:
        SSL контекст
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_file, key_file)
    
    # Настройки безопасности
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
    
    return context

def setup_https_redirect_middleware():
    """
    Middleware для перенаправления HTTP на HTTPS
    """
    from fastapi import Request, Response
    from fastapi.responses import RedirectResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    
    class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # В development можем пропустить редирект для некоторых путей
            if request.url.scheme == "http" and not request.url.path.startswith("/health"):
                # Формируем HTTPS URL
                https_url = request.url.replace(scheme="https", port=8443)
                return RedirectResponse(url=str(https_url), status_code=301)
            
            response = await call_next(request)
            return response
    
    return HTTPSRedirectMiddleware

# Импорт для создания IP адреса
import ipaddress 