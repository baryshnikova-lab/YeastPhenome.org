from django.shortcuts import render
from django.db.models import Q

from yeastphenome.forms import SearchForm

from papers.models import Paper
from conditions.models import ConditionSet
from phenotypes.models import Observable2, Phenotype
from datasets.models import Dataset


def get_latest_stats():

    papers_queryset = Paper.objects.all()
    phenotypes_queryset = Phenotype.objects.all()
    conditions_queryset = ConditionSet.objects.all()
    datasets_queryset = Dataset.objects.all()

    # Total number of papers to process
    f = Q(latest_data_status__status__status_name__in=['not relevant', 'request abandoned', 'not available'])
    papers_nr = papers_queryset.exclude(f).count()

    # Latest modified paper
    updated_on = papers_queryset.latest().modified_on

    # Number of hopeless papers
    f = Q(latest_data_status__status__status_name__in=['request abandoned', 'not available'])
    papers_hopeless_nr = papers_queryset.filter(f).count()

    # Number of papers processed and loaded
    f = Q(latest_data_status__status__status_name__exact='loaded') & \
        Q(latest_tested_status__status__status_name__in=['loaded', 'request abandoned', 'not available'])
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

    context = {'papers_nr': papers_nr, 'papers_hopeless_nr': papers_hopeless_nr,
               'papers_processed_nr': papers_processed_nr,
               'phenotypes_nr': phenotypes_nr, 'conditions_nr': conditions_nr,
               'datasets_nr': datasets_nr,
               'updated_on': updated_on}

    return context


def index(request):

    form = SearchForm()

    context = get_latest_stats()
    context['form'] = form

    return render(request, 'yeastphenome/index.html', context)


def about(request):

    context = get_latest_stats()

    return render(request, 'yeastphenome/about.html', context)
