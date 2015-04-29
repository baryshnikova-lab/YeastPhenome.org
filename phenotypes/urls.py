from django.conf.urls import patterns, url

from phenotypes import views

urlpatterns = patterns('',
    url(r'^$', views.ObservableIndexView.as_view(), name='index'),
    url(r'^(?P<pk>\d+)/$', views.ObservableDetailView.as_view(), name='detail'),
)
