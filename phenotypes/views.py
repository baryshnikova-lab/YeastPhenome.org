from django.shortcuts import render

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.core import serializers
from django.views import generic
from django.views.generic.base import TemplateView
from django.db.models import Count
from django.http import HttpResponse

from phenotypes.models import Observable2

# class PhenotypeStatsView(TemplateView):
#     template_name = 'phenotypes/stats.html'
#
#     def get_context_data(self, **kwargs):
#         context = super(PhenotypeStatsView, self).get_context_data(**kwargs)
#         datasets = Phenotype.objects.annotate(num_pap)
#         data2 = serializers.serialize('json', Phenotype.objects.annotate(num_papers=Count('dataset')))
#         context['stats'] = data2
#         return context


class ObservableIndexView(generic.ListView):
    model = Observable2
    template_name = 'phenotypes/index.html'
    context_object_name = 'nodes'
    queryset = Observable2.objects.all()


class ObservableDetailView(generic.DetailView):
	model = Observable2
	template_name = 'phenotypes/detail.html'
