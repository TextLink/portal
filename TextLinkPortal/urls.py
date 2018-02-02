"""TextLinkPortal URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""

from django.conf.urls import url
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt

from portal import views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^home/', views.home, name='home'),
    url(r'^get_connectives_wrt_language', csrf_exempt(views.get_connectives_wrt_language),
        name='get_connectives_wrt_language'),
    url(r'^get_sense_wrt_connective', csrf_exempt(views.get_senses_wrt_connective),
        name='get_senses_wrt_connective'),
    url(r'^get_senses_wrt_language', csrf_exempt(views.get_senses_wrt_language),
        name='get_senses_wrt_language'),
    url(r'^get_connectives_wrt_sense', csrf_exempt(views.get_connectives_wrt_sense),
        name='get_connectives_wrt_sense'),

    url(r'^upload_annotations/$', views.upload_annotations, name='upload_annotations.html'),

    url(r'^upload/search_page/', csrf_exempt(views.search_page_rest), name='search_page.html'),
    url(r'^upload/search_sense_rest', csrf_exempt(views.search_sense_rest), name='search_sense_rest'),

    url(r'^highlight_rest', csrf_exempt(views.highlight_rest), name='highlight_rest'),
    url(r'^download/', csrf_exempt(views.download_excel), name='download'),

    url(r'^ted_mdb/', csrf_exempt(views.ted_mdb), name='ted_mdb.html'),
    url(r'^ted_mdb_rest', csrf_exempt(views.ted_mdb_rest), name='ted_mdb_rest'),
    url(r'^ted_mdb_get_aligned', csrf_exempt(views.ted_mdb_get_aligned), name='ted_mdb_get_aligned'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
