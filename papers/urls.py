from django.conf.urls import patterns, url
from . import views
from papers import views


urlpatterns = [
    url(r'^$', views.paper_list_view, name='all'),
    url(r'^(?P<pk>\d+)/$', views.PaperDetailView.as_view(), name='detail'),

    # To get a zip file of data
    url(r'^(?P<pk>\d+).zip$', views.zipo, name='zipo'),
    url(r'^(?P<paper_id>\d+)/YeastPhenome_(\d+)_datasets_list.txt$', views.paper_datasets, name='paper_datasets'),
    url(r'^(?P<paper_id>\d+)/YeastPhenome_(\d+)_(?P<dataset_id>\d+)_data.txt$', views.dataset_data, name='dataset_data'),
]
