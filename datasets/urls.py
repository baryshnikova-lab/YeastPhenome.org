from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<domain>papers)/(?P<id>\d+)/', views.data, name='data'),
    url(r'^(?P<domain>datasets)/(?P<id>\d+)/', views.data, name='data'),
    url(r'^(?P<domain>conditions)/(?P<id>\d+)/', views.data, name='data'),
    url(r'^conditions/(?P<domain>chebi)/(?P<id>\d+)/', views.data, name='data'),
    url(r'^(?P<domain>phenotypes)/(?P<id>\d+)/', views.data, name='data'),
    url(r'^(?P<pk>\d+)/$', views.DatasetDetailView.as_view(), name='detail'),
    url(r'^class/growth/$', views.datasets_growth, name='growth'),
    url(r'^class/human/$', views.datasets_human, name='human'),
    url(r'^download/all/', views.download_all, name='download_all'),
    url(r'^download/', views.download, name='download'),
]
