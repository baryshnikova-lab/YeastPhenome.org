from django.views import generic
from django.views.generic.base import TemplateView
from django.db.models import Count
from django.http import HttpResponse
from django.conf import settings
import json

from django.shortcuts import render, get_object_or_404
from django.db.models import Q

from conditions.models import ConditionType
from papers.models import Data, Dataset

from conditions.forms import SearchForm


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
        return context


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


def data(request, conditiontype_id):
    conditiontype = get_object_or_404(ConditionType, pk=conditiontype_id)
    datasets = conditiontype.datasets()
    data = Data.objects.filter(dataset_id__in=datasets.values('id')).all()

    orfs = list(data.values_list('orf', flat=True).distinct())
    datasets_ids = list(data.values_list('dataset_id', flat=True).order_by('dataset__paper').distinct())
    matrix = [[None] * len(datasets_ids) for i in orfs]

    for datapoint in data:
        i = orfs.index(datapoint.orf)
        j = datasets_ids.index(datapoint.dataset_id)
        matrix[i][j] = datapoint.value

    txt1 = u'# Condition: %s (ID %s)\n' % (conditiontype, conditiontype.id)
    txt2 = '\t' + '\t'.join([u'%s' % str(get_object_or_404(Dataset, pk=dataset_id)) for dataset_id in datasets_ids]) + '\n'

    data_row = []
    for i, orf in enumerate(orfs):
        new_row = orf + '\t' + '\t'.join([str(val) for val in matrix[i]])
        print(new_row)
        data_row.append(new_row)

    txt3 = '\n'.join(data_row)

    response = HttpResponse(txt1+txt2+txt3, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="%s_condition_%d_data.txt"' % (settings.DOWNLOAD_PREFIX, conditiontype.id)

    return response