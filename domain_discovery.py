#!/usr/bin/env python3
import sys
import json

def get_domains_from_file(file_path):
    try:
        with open(file_path, 'r') as f:
            domains = [line.strip() for line in f if line.strip()]
        return domains
    except Exception:
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: domain_discovery.py <file_path>"}))
        sys.exit(1)

    file_path = sys.argv[1]
    domains = get_domains_from_file(file_path)
    discovery_data = {
        "data": [{"{#DOMAIN}": domain} for domain in domains]
    }
    print(json.dumps(discovery_data))