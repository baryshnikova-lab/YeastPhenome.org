from django.conf.urls import patterns, include, url
import papers
from . import views

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^about/$', views.about, name='about'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^papers/', include('papers.urls', namespace="papers")),
    url(r'^phenotypes/', include('phenotypes.urls', namespace="phenotypes")),
    url(r'^conditions/', include('conditions.urls', namespace="conditions")),
    url(r'^data/', include('datasets.urls', namespace="datasets")),
    url(r'^contributors/', papers.views.ContributorsListView.as_view(), name="contributors")
]
