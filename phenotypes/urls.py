from django.conf.urls import patterns, url
from . import views

urlpatterns = [
    url(r'^$', views.ObservableIndexView.as_view(), name='index'),
    url(r'^(?P<pk>\d+)/$', views.ObservableDetailView.as_view(), name='detail'),
    url(r'^circle/$', views.D3Packing.as_view(), name="d3circle"),
    url(r'^square/$', views.D3Packing.as_view(), name="d3square")
]
