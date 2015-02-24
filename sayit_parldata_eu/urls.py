import re
import sys

from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.decorators.cache import cache_page

# Admin section
## from django.contrib import admin
## admin.autodiscover()

from speeches.views import SpeakerList, SpeakerView, SectionView
from .views import RecentView

urlpatterns = staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# If we're running test, then we need to serve static files even though DEBUG
# is false to prevent lots of 404s. So do what staticfiles_urlpatterns would do.
if 'test' in sys.argv:
    static_url = re.escape(settings.STATIC_URL.lstrip('/'))
    urlpatterns += patterns(
        '',
        url(r'^%s(?P<path>.*)$' % static_url, 'django.contrib.staticfiles.views.serve', {
            'insecure': True,
        }),
        url('^(?P<path>favicon\.ico)$', 'django.contrib.staticfiles.views.serve', {
            'insecure': True,
        }),
    )

urlpatterns += patterns(
    '',
##    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
##    (r'^admin/', include(admin.site.urls)),

##    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
##    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout'),

    url(r'^speeches$', RecentView.as_view(), name='recent-view'),

    # set caching for some views of the speeches app
    url(r'^speakers$', cache_page(10*365*86400)(SpeakerList.as_view()), name='speaker-list'),
    url(r'^speaker/(?P<slug>.+)$', SpeakerView.as_view(), name='speaker-view'),
    url(r'^(?P<full_slug>.+)$', cache_page(10*365*86400)(SectionView.as_view()), name='section-view'),

    url(r'^', include('speeches.urls', app_name='speeches', namespace='speeches')),
)
