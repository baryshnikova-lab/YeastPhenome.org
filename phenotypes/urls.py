from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.ObservableIndexView.as_view(), name='index'),
    url(r'^(?P<pk>\d+)/$', views.ObservableDetailView.as_view(), name='detail'),
]
