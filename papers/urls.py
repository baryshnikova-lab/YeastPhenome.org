from django.conf.urls import patterns, url
from . import views

urlpatterns = [
    url(r'^$', views.PaperAllIndexView.as_view(), name='all'),
    # url(r'^haploid/$', views.PaperHaploidIndexView.as_view(), name='haploid'),
    # url(r'^diploid/homozygous/$', views.PaperDiploidHomozygousIndexView.as_view(), name='diploid homozygous'),
    # url(r'^diploid/heterozygous/$', views.PaperDiploidHeterozygousIndexView.as_view(), name='diploid heterozygous'),
    # url(r'^quantitative/$', views.PaperQuantitativeIndexView.as_view(), name='quantitative'),
    # url(r'^discrete/$', views.PaperDiscreteIndexView.as_view(), name='discrete'),
    url(r'^(?P<pk>\d+)/$', views.PaperDetailView.as_view(), name='detail'),

    # To get a zip file of data
    url(r'^(?P<pk>\d+).zip$', views.zipo, name='zipo'),
]
