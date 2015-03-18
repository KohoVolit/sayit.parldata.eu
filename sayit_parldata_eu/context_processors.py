from django.conf import settings

def exposed_settings(request):
    exposed = {}
    for s in getattr(settings, "SETTINGS_EXPOSED_TO_TEMPLATES", ()):
        exposed[s] = getattr(settings, s, None)
    return {'settings': exposed}
