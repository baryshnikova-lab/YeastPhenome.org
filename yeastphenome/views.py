from django.shortcuts import render
from django.db.models import Q

from yeastphenome.forms import SearchForm

from papers.models import Paper
from conditions.models import Condition
from phenotypes.models import Observable2


def index(request):

    queryset = Paper.objects.all()
    latest_paper = queryset.latest().modified_on

    form = SearchForm()

    # Exclude the papers marked as "not relevant"
    f = Q(data_statuses__status_name__exact='not relevant') | Q(tested_statuses__status_name__exact='not relevant')
    queryset = queryset.exclude(f)

    context = {
        'paper_num_total': queryset.count(),
        'phenotype_num_total': Observable2.objects.exclude(phenotype__dataset = None).count(),
        'condition_num': Condition.objects.all().count(),
        'updated': latest_paper,
        'form': form,
    }

    return render(request, 'yeastphenome/index.html', context)


def about(request):
    return render(request, 'yeastphenome/about.html')
