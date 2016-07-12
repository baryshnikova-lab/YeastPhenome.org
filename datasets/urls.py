from django.conf.urls import patterns, url
from . import views

urlpatterns = [
    url(r'^(?P<domain>papers)/(?P<id>\d+)/', views.data, name='data'),
    url(r'^(?P<domain>datasets)/(?P<id>\d+)/', views.data, name='data'),
    url(r'^(?P<domain>conditions)/(?P<id>\d+)/', views.data, name='data'),
    url(r'^(?P<domain>chebi)/(?P<id>\d+)/', views.data, name='data'),
    url(r'^(?P<domain>phenotypes)/(?P<id>\d+)/', views.data, name='data'),
]
