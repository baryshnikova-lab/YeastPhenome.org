from django.conf.urls import patterns, url
from . import views

urlpatterns = [
    url(r'^$', views.ConditionIndexView.as_view(), name='index'),
    url(r'^(?P<pk>\d+)/$', views.ConditionDetailView.as_view(), name='detail'),
    url(r'^/stats/$', views.ConditionGraphView.as_view(), name="graph"),
]
