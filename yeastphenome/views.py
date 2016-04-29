from django.shortcuts import render

from yeastphenome.forms import SearchForm

from papers.models import Paper
from conditions.models import Condition
from phenotypes.models import Observable2


def index(request):
    latest_paper = Paper.objects.all().latest().modified_on

    form = SearchForm()

    context = {
        'paper_num_total': Paper.objects.all().count(),
        'phenotype_num_total': Observable2.objects.exclude(phenotype__dataset = None).count(),
        'condition_num': Condition.objects.all().count(),
        'updated': latest_paper,
        'form': form,
    }

    return render(request, 'yeastphenome/index.html', context)


def about(request):
    return render(request, 'yeastphenome/about.html')
