from django.conf.urls import patterns, include, url
from papers import views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	url(r'^$', 'yeastphenome.views.index', name='index'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^papers/', include('papers.urls', namespace="papers")),
    url(r'^phenotypes/', include('phenotypes.urls', namespace="phenotypes")),
    url(r'^conditions/', include('conditions.urls', namespace="conditions")),
    url(r'^contributors/', views.ContributorsListView.as_view(), name="contributors"),
)
