import os
import re

from django.conf import settings

def get_subdomains():
    """Returns list of all subdomains present in `/subdomains` subdirectory."""
    subdomains = (f[:-3]
        for f in os.listdir(settings.SUBDOMAINS_DIR)
        if os.path.isfile(os.path.join(settings.SUBDOMAINS_DIR, f)) and not f.startswith('_')
    )
    return subdomains
