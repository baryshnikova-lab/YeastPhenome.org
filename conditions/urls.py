from django.conf.urls import patterns, url
from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<pk>\d+)/$', views.ConditionDetailView.as_view(), name='detail'),
    url(r'^bubble/$', views.D3Packing.as_view(), name="bubble"),
    url(r'^(?P<conditiontype_id>\d+)/YeastPhenome_condition_(\d+)_data.txt$', views.data, name='data'),

]
