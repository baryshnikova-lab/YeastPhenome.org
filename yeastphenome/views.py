from django.shortcuts import render
from django.db.models import Q

from yeastphenome.forms import SearchForm

from papers.models import Paper
from conditions.models import ConditionSet
from phenotypes.models import Observable2, Phenotype
from datasets.models import Dataset


def index(request):

    queryset = Paper.objects.all()
    latest_paper = queryset.latest().modified_on

    form = SearchForm()

    # Exclude the papers marked as "not relevant"
    f = Q(latest_data_status__status__status_name__exact='not relevant') | \
        Q(latest_tested_status__status__status_name__exact='not relevant')
    queryset = queryset.exclude(f)

    context = {
        'paper_num_total': queryset.count(),
        'phenotype_num_total': Observable2.objects.exclude(phenotype__dataset__isnull=True).count(),
        'condition_num': ConditionSet.objects.all().count(),
        'updated': latest_paper,
        'form': form,
    }

    return render(request, 'yeastphenome/index.html', context)


def about(request):

    papers_queryset = Paper.objects.all()
    phenotypes_queryset = Phenotype.objects.all()
    conditions_queryset = ConditionSet.objects.all()
    datasets_queryset = Dataset.objects.all()

    # Total number of papers to process
    f = Q(latest_data_status__status__status_name__exact='not relevant') | \
        Q(latest_tested_status__status__status_name__exact='not relevant')
    papers_nr = papers_queryset.exclude(f).count()

    # Number of papers processed and loaded
    f = Q(latest_data_status__status__status_name__exact='loaded') & \
        Q(latest_tested_status__status__status_name__in=['loaded', 'abandoned', 'not available'])
    papers_queryset = papers_queryset.filter(f)
    papers_processed_nr = papers_queryset.count()

    # Number of phenotypes
    f = Q(dataset__paper__in=papers_queryset)
    phenotypes_nr = phenotypes_queryset.filter(f).distinct().count()

    # Number of conditions
    f = Q(dataset__paper__in=papers_queryset)
    conditions_nr = conditions_queryset.filter(f).distinct().count()

    # Number of datasets
    f = Q(paper__in=papers_queryset)
    datasets_nr = datasets_queryset.filter(f).distinct().count()

    context = {'papers_nr': papers_nr, 'papers_processed_nr': papers_processed_nr,
               'phenotypes_nr': phenotypes_nr, 'conditions_nr': conditions_nr,
               'datasets_nr': datasets_nr}

    return render(request, 'yeastphenome/about.html', context)
