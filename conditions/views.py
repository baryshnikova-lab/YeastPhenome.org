from django.views import generic
from django.views.generic.base import TemplateView
from django.db.models import Count
from django.http import HttpResponse
from django.conf import settings
import json

from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from conditions.models import ConditionType
from datasets.models import Dataset, Data

from conditions.forms import SearchForm

from libchebipy import ChebiEntity


def index(request):

    if 'q' in request.GET:
        form = SearchForm(request.GET)
        queryset = ConditionType.objects.order_by('name')
        q = request.GET['q']
        f = Q(name__icontains=q) | Q(other_names__icontains=q) | Q(chebi_name__contains=q) | Q(pubchem_name__contains=q)
        queryset = queryset.filter(f)

        return render(request, 'conditions/index.html', {
            'conditiontype_list': queryset,
            'form': form,
            'q': q,
        })
    else:
        form = SearchForm()

        return render(request, 'conditions/index.html', {
            'form': form,
        })


class ConditionDetailView(generic.DetailView):
    model = ConditionType
    template_name = 'conditions/detail.html'

    def get_context_data(self, **kwargs):
        context = super(ConditionDetailView, self).get_context_data(**kwargs)
        context['DOWNLOAD_PREFIX'] = settings.DOWNLOAD_PREFIX
        context['USER_AUTH'] = self.request.user.is_authenticated()
        return context


def conditionclass(request, class_id):
    class_entity = ChebiEntity('CHEBI:' + str(class_id))
    class_name = class_entity.get_name()
    children = []
    for relation in class_entity.get_incomings():
        if relation.get_type() == 'has_role':
            tid = relation.get_target_chebi_id()
            tid = int(filter(str.isdigit, tid))
            children.append(tid)

    conditiontypes = ConditionType.objects.filter(chebi_id__in=children)
    return render(request, 'conditions/class.html', {
        'class_id': class_id,
        'class_name': class_name,
        'conditiontypes': conditiontypes,
        'DOWNLOAD_PREFIX': settings.DOWNLOAD_PREFIX,
        'USER_AUTH': request.user.is_authenticated()
    })


class D3Packing(generic.ListView):
    model = ConditionType
    template_name = 'conditions/d3.html'

    def flare(self,ctl):
        out={'name':'conditions','children':[]}
        for ct in ctl:
            paper_count=len(ct.paper_list())
            if 0<paper_count:
                out['children'].append({
                    'name':ct.__unicode__(),
                    'size':paper_count,
                    'id':ct.id,
                })
        return out

    def get_context_data(self,**kwargs):
        context = super(generic.ListView,self).get_context_data(**kwargs)
        # Luckily json is based on JavaScript so we just dump it out with this.
        context['flare'] = json.dumps(self.flare(context['conditiontype_list']))
        return context