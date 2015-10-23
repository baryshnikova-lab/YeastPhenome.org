import json
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

class D3Packing(generic.ListView):
    model = Observable2
    template_name='phenotypes/d3.html'
    context_object_name = 'nodes'

    def aux(self,node):
        out = {
            'name':node.name,
            'size':len(node.paper_list()),
            'dsize':len(node.paper_list()),
            'id':node.id,
           }
        if node.is_leaf_node():
            return out
        out['children'] = []

        for child in node.get_children():
            decedents=self.aux(child);
            if decedents['dsize'] > 0:
                out['dsize'] += decedents['dsize'];
                out['children'].append(decedents)
        return out

    def flare(self,nodes):
        out={'name':'phenotypes','children':[]}
        for node in nodes:
            if None==node.parent:
                out['children'].append(self.aux(node))
        return out

    def get_context_data(self,**kwargs):
        context = super(generic.ListView,self).get_context_data(**kwargs)
        # Luckly json is based on JavaScript so we just dump it out with this.
        context['flare'] = json.dumps(self.flare(context['nodes']),indent=1)
        return context
