import json
import re

from itertools import chain

from django.views import generic
from django.views.generic.base import TemplateView
from django.db.models import Count
from django.http import HttpResponse
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from conditions.models import ConditionType, ConditionSet, Medium
from datasets.models import Dataset, Data

from conditions.forms import SearchForm

from libchebipy import ChebiEntity


def index(request):

    if 'q' in request.GET:

        form = SearchForm(request.GET)
        q = request.GET['q'].strip()

        f = Q(systematic_name__icontains=q) | \
            Q(common_name__icontains=q) | \
            Q(display_name__icontains=q) | \
            Q(conditions__type__name__icontains=q) | \
            Q(conditions__type__other_names__icontains=q) | \
            Q(conditions__type__chebi_name__icontains=q) | \
            Q(conditions__type__pubchem_name__icontains=q)

        g = Count('dataset', filter=~Q(paper__latest_data_status__status__name='not relevant'))

        queryset1 = ConditionSet.objects.all()
        queryset1 = queryset1.filter(f).annotate(num_datasets=g).filter(num_datasets__gte=0).distinct()

        queryset2 = Medium.objects.all()
        queryset2 = queryset2.filter(f).annotate(num_datasets=g).filter(num_datasets__gte=0).distinct()

        queryset = list(chain(queryset1, queryset2))

        return render(request, 'conditions/index.html', {
            'queryset': queryset,
            'form': form,
            'q': q,
        })
    else:
        form = SearchForm()

        return render(request, 'conditions/index.html', {
            'form': form,
        })


class ConditiontypeDetailView(generic.DetailView):
    model = ConditionType
    template_name = 'conditions/detail.html'

    def get_context_data(self, **kwargs):
        context = super(ConditiontypeDetailView, self).get_context_data(**kwargs)
        context['DOWNLOAD_PREFIX'] = settings.DOWNLOAD_PREFIX
        context['USER_AUTH'] = self.request.user.is_authenticated()
        context['papers'] = context['object'].datasets
        context['id'] = context['object'].id
        return context


def conditionclass(request, class_id):
    class_entity = ChebiEntity('CHEBI:' + str(class_id))
    class_name = class_entity.get_name()
    children = []
    for relation in class_entity.get_incomings():
        if relation.get_type() == 'has_role':
            tid = relation.get_target_chebi_id()
            tid = re.search('(?<=CHEBI:)(\d)*', tid)
            tid = int(tid.group(0))
            children.append(tid)

    conditiontypes = ConditionType.objects.filter(chebi_id__in=children)
    datasets = Dataset.objects.filter(conditionset__conditions__type__in=conditiontypes)\
        .exclude(paper__latest_data_status__status__name='not relevant').distinct()
    return render(request, 'conditions/class.html', {
        'id': class_id,
        'class_name': class_name,
        'conditiontypes': conditiontypes,
        'papers': datasets,
        'DOWNLOAD_PREFIX': settings.DOWNLOAD_PREFIX,
        'USER_AUTH': request.user.is_authenticated()
    })


class MediumDetailView(generic.DetailView):
    model = Medium
    template_name = 'conditions/conditionset_medium_detail.html'

    def get_context_data(self, **kwargs):
        context = super(MediumDetailView, self).get_context_data(**kwargs)
        context['DOWNLOAD_PREFIX'] = settings.DOWNLOAD_PREFIX
        context['USER_AUTH'] = self.request.user.is_authenticated()
        context['papers'] = context['object'].datasets
        context['id'] = context['object'].id
        return context


class ConditionSetDetailView(generic.DetailView):
    model = ConditionSet
    template_name = 'conditions/conditionset_medium_detail.html'

    def get_context_data(self, **kwargs):
        context = super(ConditionSetDetailView, self).get_context_data(**kwargs)
        context['DOWNLOAD_PREFIX'] = settings.DOWNLOAD_PREFIX
        context['USER_AUTH'] = self.request.user.is_authenticated()
        context['papers'] = context['object'].datasets
        context['id'] = context['object'].id
        return context


