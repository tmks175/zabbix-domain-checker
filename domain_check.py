#!/usr/bin/env python3
import sys
import whois
import ssl, socket
import json
from datetime import datetime

def get_domain_expiry(domain):
    try:
        w = whois.whois(domain)
        exp_date = w.expiration_date
        if isinstance(exp_date, list):
            exp_date = exp_date[0]
        if exp_date:
            return (exp_date - datetime.utcnow()).days
    except Exception:
        return 0
    return 0

def get_ssl_expiry(domain):
    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=11) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
        expire_date = datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
        return (expire_date - datetime.utcnow()).days
    except Exception:
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