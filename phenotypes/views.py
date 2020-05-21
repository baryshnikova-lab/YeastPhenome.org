from django.views import generic
from django.conf import settings

from phenotypes.models import Observable


class ObservableIndexView(generic.ListView):
    model = Observable
    template_name = 'phenotypes/index.html'
    context_object_name = 'observables'
    queryset = Observable.objects.order_by('name').all()


class ObservableDetailView(generic.DetailView):
    model = Observable
    template_name = 'phenotypes/detail.html'

    def get_context_data(self, **kwargs):
        context = super(ObservableDetailView, self).get_context_data(**kwargs)
        context['DOWNLOAD_PREFIX'] = settings.DOWNLOAD_PREFIX
        context['USER_AUTH'] = self.request.user.is_authenticated()
        context['datasets'] = context['object'].datasets
        context['id'] = context['object'].id
        return context

