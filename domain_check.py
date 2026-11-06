#!/usr/bin/env python3
import sys
import whois
import ssl
import socket
import json
import time
from datetime import datetime

WHOIS_RETRIES = 2
WHOIS_DELAY = 3

SSL_RETRIES = 2
SSL_DELAY = 3
CONNECT_TIMEOUT = 5

# Проверка доступности порта
def is_port_open(domain, port=443, timeout=3):
    try:
        with socket.create_connection((domain, port), timeout=timeout):
            return True
    except Exception:
        return False

def get_domain_expiry(domain):
    for attempt in range(1, WHOIS_RETRIES + 1):
        try:
            w = whois.whois(domain)
            exp_date = w.expiration_date
            if isinstance(exp_date, list):
                exp_date = exp_date[0]
            if exp_date:
                return (exp_date - datetime.utcnow()).days
        except Exception:
            if attempt < WHOIS_RETRIES:
                time.sleep(WHOIS_DELAY)
            else:
                return 0
    return 0

def get_ssl_expiry(domain):
    # Если порт недоступен - не тратим время на ретраи
    if not is_port_open(domain, 443, timeout=3):
        return 0

    for attempt in range(1, SSL_RETRIES + 1):
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=CONNECT_TIMEOUT) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
            expire_date = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
            return (expire_date - datetime.utcnow()).days
        except Exception:
            if attempt < SSL_RETRIES:
                time.sleep(SSL_DELAY)
            else:
                return 0
    return 0

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: domain_check.py <domain>"}))
        sys.exit(1)

    domain = sys.argv[1]
    result = {
        "domain_days": get_domain_expiry(domain),
        "ssl_days": get_ssl_expiry(domain)
    }
    print(json.dumps(result))
