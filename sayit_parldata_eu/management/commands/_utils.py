import os
import re

from django.conf import settings

def get_all_parliaments():
    """Returns list of all parliaments present in `/subdomains` subdirectory as
    a list of tuples (country_code, parliament_code)."""
    parliaments = []
    for fname in os.listdir(settings.SUBDOMAINS_DIR):
        pathname = os.path.join(settings.SUBDOMAINS_DIR, fname)
        if not os.path.isfile(pathname):
            continue
        with open(pathname) as f:
            content = f.read()
        country = re.search(r'COUNTRY_CODE\s*=\s*[\'\"](\w+)[\'\"]', content)
        parl = re.search(r'PARLIAMENT_CODE\s*=\s*[\'\"](\w+)[\'\"]', content)
        if country is not None and parl is not None:
            parliaments.append((country.group(1), parl.group(1)))
    return parliaments


def get_subdomains():
    """Returns list of all subdomains present in `/subdomains` subdirectory."""
    subdomains = (f[:-3]
        for f in os.listdir(settings.SUBDOMAINS_DIR)
        if os.path.isfile(os.path.join(settings.SUBDOMAINS_DIR, f)) and not f.startswith('_')
    )
    return subdomains
