from django.shortcuts import render
from django.db.models import Q, F, Count, Sum, Case, When
from django.db import models

import numpy as np

from yeastphenome.forms import SearchForm

from papers.models import Paper
from conditions.models import ConditionSet, ConditionType
from phenotypes.models import Phenotype
from datasets.models import Dataset


def get_latest_stats():

    papers_qs = Paper.objects.all()
    phenotypes_qs = Phenotype.objects.all()
    conditions_qs = ConditionSet.objects.all()
    conditiontypes_qs = ConditionType.objects.all()
    datasets_qs = Dataset.objects.all()

    # Total number of papers to process
    f = Q(latest_data_status__status__is_valid=True)
    papers_nr = papers_qs.filter(f).count()

    # Latest modified paper
    updated_on = papers_qs.latest().modified_on

    # Number of hopeless papers
    f = Q(latest_data_status__status__name__in=['request abandoned', 'not available'])
    papers_hopeless_nr = papers_qs.filter(f).count()

    # Number of labs
    f = Q(latest_data_status__status__name__in=['not relevant'])
    labs_nr = papers_qs.exclude(f).values('last_author').distinct().count()

    # Number of papers processed and loaded
    f = Q(latest_data_status__status__name__exact='loaded') & \
        Q(latest_tested_status__status__name__in=['loaded', 'request abandoned', 'not available'])
    papers_processed_qs = papers_qs.filter(f)
    papers_processed_nr = papers_processed_qs.count()

    # Number of phenotypes
    f = Q(dataset__paper__in=papers_processed_qs)
    phenotypes_nr = phenotypes_qs.filter(f).distinct().count()

    # Number of conditions
    f = Q(dataset__paper__in=papers_processed_qs)
    conditions_nr = conditions_qs.filter(f).distinct().count()

    # Number of papers (total)
    f = Q(paper__in=papers_processed_qs)
    datasets_nr = datasets_qs.filter(f).distinct().count()

    # --- Conditions ---
    top_conditiontypes = conditiontypes_qs. \
        annotate(nr_papers=Count('condition__conditionset__dataset__paper', distinct=True)).\
        annotate(
        nr_datasets=Sum(Case(
            When(condition__conditionset__dataset__data_available__shortname__in=['q', 'qofh', 'd'], then=1),
            default=0, output_field=models.IntegerField())),
        nr_datasets_q=Sum(Case(
            When(condition__conditionset__dataset__data_available__shortname='q', then=1),
            default=0, output_field=models.IntegerField())),
        nr_datasets_d=Sum(Case(
            When(condition__conditionset__dataset__data_available__shortname='d', then=1),
            default=0, output_field=models.IntegerField())),
        nr_datasets_qofh=Sum(Case(
            When(condition__conditionset__dataset__data_available__shortname='qofh', then=1),
            default=0, output_field=models.IntegerField()))). \
        exclude(name__in=['standard', 'time']). \
        order_by('-nr_papers')


    # top_conditiontypes_q = top_conditiontypes. \
    #     annotate(nr_datasets_q=Count(condition__conditionset__dataset__paper__data_available__shortname='q'))

    # --- Phenotypes ----
    p = Q(paper__in=papers_processed_qs)
    c1 = Q(collection__shortname__in=['hap a', 'hap alpha', 'hom', 'hap ?',
                                     'hap a/hap alpha/hom', 'hap a/hap alpha', 'hap a/hom'])
    c2 = Q(collection__shortname__in=['het'])
    gr = Q(phenotype__name__contains='growth')
    exp = Q(phenotype__name__contains='gene expression')
    datasets_processed_homhap_qs = datasets_qs.filter(p & c1)
    datasets_processed_het_qs = datasets_qs.filter(p & c2)

    datasets_nr_processed_homhap = datasets_processed_homhap_qs.count()
    papers_nr_processed_homhap = datasets_processed_homhap_qs.values('paper_id').distinct().count()

    datasets_nr_processed_het = datasets_processed_het_qs.count()
    papers_nr_processed_het = datasets_processed_het_qs.values('paper_id').distinct().count()

    datasets_nr_processed_homhap_growth = datasets_processed_homhap_qs.filter(gr).count()
    papers_nr_processed_homhap_growth = datasets_processed_homhap_qs.filter(gr).values('paper_id').distinct().count()

    datasets_nr_processed_het_growth = datasets_processed_het_qs.filter(gr).count()
    papers_nr_processed_het_growth = datasets_processed_het_qs.filter(gr).values('paper_id').distinct().count()

    datasets_nr_processed_homhap_expression = datasets_processed_homhap_qs.filter(exp).count()
    papers_nr_processed_homhap_expression = datasets_processed_homhap_qs.filter(exp).values('paper_id').distinct().count()

    datasets_nr_processed_het_expression = datasets_processed_het_qs.filter(exp).count()
    papers_nr_processed_het_expression = datasets_processed_het_qs.filter(exp).values('paper_id').distinct().count()

    datasets_nr_processed_homhap_other = datasets_processed_homhap_qs.exclude(gr).exclude(exp).count()
    papers_nr_processed_homhap_other = datasets_processed_homhap_qs.exclude(gr).exclude(exp).values('paper_id').distinct().count()

    datasets_nr_processed_het_other = datasets_processed_het_qs.exclude(gr).exclude(exp).count()
    papers_nr_processed_het_other = datasets_processed_het_qs.exclude(gr).exclude(exp).values('paper_id').distinct().count()


    # --- Collections ----
    f = Q(paper__in=papers_processed_qs)

    c = Q(collection__shortname__in=['hap a'])
    datasets_nr_hap_a = datasets_qs.filter(f & c).distinct().count()
    datasets_prc_hap_a = int(np.rint(100 * datasets_nr_hap_a / datasets_nr))

    c = Q(collection__shortname__in=['hap alpha'])
    datasets_nr_hap_alpha = datasets_qs.filter(f & c).distinct().count()
    datasets_prc_hap_alpha = int(np.rint(100 * datasets_nr_hap_alpha / datasets_nr))

    c = Q(collection__shortname__in=['hom'])
    datasets_nr_hom = datasets_qs.filter(f & c).distinct().count()
    datasets_prc_hom = int(np.rint(100 * datasets_nr_hom / datasets_nr))

    c = Q(collection__shortname__in=['het'])
    datasets_nr_het = datasets_qs.filter(f & c).distinct().count()
    datasets_prc_het = int(np.rint(100 * datasets_nr_het / datasets_nr))

    c = Q(collection__shortname__in=['hap ?', 'hap a/hap alpha/hom', 'hap a/hap alpha', 'hap a/hom', 'hom/het?',
                                     'hom/het', 'hap a/het', 'hap ?/hom/het'])
    datasets_nr_mix = datasets_qs.filter(f & c).distinct().count()
    datasets_prc_mix = int(np.rint(100 * datasets_nr_mix / datasets_nr))

    datasets_nr_collections_total = datasets_nr_hap_a + datasets_nr_hap_alpha + \
                                    datasets_nr_hom + datasets_nr_het + datasets_nr_mix

    # c = Q(collection__shortname__in=['hap a', 'hap alpha', 'hom', 'het', 'hap ?', 'hap a/hap alpha/hom',
    #                                  'hap a/hap alpha', 'hap a/hom', 'hom/het?',
    #                                  'hom/het', 'hap a/het', 'hap ?/hom/het'])
    # missing = datasets_queryset.filter(f).exclude(c)


    # --- Data types ---
    f = Q(paper__in=papers_processed_qs) & \
        Q(data_available__shortname='q')
    datasets_nr_q = datasets_qs.filter(f).distinct().count()
    datasets_prc_q = int(np.rint(100 * datasets_nr_q / datasets_nr))

    f = Q(paper__in=papers_processed_qs) & \
        Q(data_available__shortname='qofh')
    datasets_nr_qofh = datasets_qs.filter(f).distinct().count()
    datasets_prc_qofh = int(np.rint(100 * datasets_nr_qofh / datasets_nr))

    f = Q(paper__in=papers_processed_qs) & \
        Q(data_available__shortname='d')
    datasets_nr_d = datasets_qs.filter(f).distinct().count()
    datasets_prc_d = int(np.rint(100 * datasets_nr_d / datasets_nr))

    datasets_nr_data_available_total = datasets_nr_q + datasets_nr_qofh + datasets_nr_d

    # Data recovery for haploid/homozygous diploid
    f = Q(paper__in=papers_processed_qs)

    g1 = Q(data_measured__rank__lt=F('data_published__rank'))   # papers in need of data recovery
    g2 = Q(data_available__rank__lt=F('data_published__rank'))   # papers with recovered data

    h1 = Q(tested_list_published=False)   # papers in need of tested list recovery
    h2 = Q(tested_list_published=False) & Q(tested_source_id__isnull=False)   # papers with recovered tested list

    fgh = f & (g2 | h2)   # all papers with something recovered

    datasets_nr_need_data = datasets_qs.filter(f & g1).distinct().count()
    datasets_nr_need_tested = datasets_qs.filter(f & h1).distinct().count()

    datasets_nr_recovered_all = datasets_qs.filter(fgh).distinct().count()
    datasets_nr_recovered_data = datasets_qs.filter(f & g2).distinct().count()
    datasets_nr_recovered_tested = datasets_qs.filter(f & h2).distinct().count()

    context = {'papers_nr': papers_nr, 'papers_hopeless_nr': papers_hopeless_nr,
               'labs_nr': labs_nr,
               'papers_processed_nr': papers_processed_nr,
               'phenotypes_nr': phenotypes_nr, 'conditions_nr': conditions_nr,
               'datasets_nr': datasets_nr,
               'datasets_nr_hap_a': datasets_nr_hap_a, 'datasets_prc_hap_a': datasets_prc_hap_a,
               'datasets_nr_hap_alpha': datasets_nr_hap_alpha, 'datasets_prc_hap_alpha': datasets_prc_hap_alpha,
               'datasets_nr_hom': datasets_nr_hom, 'datasets_prc_hom': datasets_prc_hom,
               'datasets_nr_het': datasets_nr_het, 'datasets_prc_het': datasets_prc_het,
               'datasets_nr_mix': datasets_nr_mix, 'datasets_prc_mix': datasets_prc_mix,
               'datasets_nr_collections_total': datasets_nr_collections_total,
               'datasets_nr_q': datasets_nr_q, 'datasets_prc_q': datasets_prc_q,
               'datasets_nr_qofh': datasets_nr_qofh, 'datasets_prc_qofh': datasets_prc_qofh,
               'datasets_nr_d': datasets_nr_d, 'datasets_prc_d': datasets_prc_d,
               'datasets_nr_data_available_total': datasets_nr_data_available_total,
               'datasets_nr_need_data': datasets_nr_need_data,
               'datasets_nr_need_tested': datasets_nr_need_tested,
               'datasets_nr_recovered_all': datasets_nr_recovered_all,
               'datasets_nr_recovered_data': datasets_nr_recovered_data,
               'datasets_nr_recovered_tested': datasets_nr_recovered_tested,
               'top_conditiontypes': top_conditiontypes[:10],
               'datasets_nr_processed_homhap': datasets_nr_processed_homhap,
               'datasets_nr_processed_homhap_growth': datasets_nr_processed_homhap_growth,
               'datasets_nr_processed_homhap_expression': datasets_nr_processed_homhap_expression,
               'datasets_nr_processed_homhap_other': datasets_nr_processed_homhap_other,
               'papers_nr_processed_homhap': papers_nr_processed_homhap,
               'papers_nr_processed_homhap_growth': papers_nr_processed_homhap_growth,
               'papers_nr_processed_homhap_expression': papers_nr_processed_homhap_expression,
               'papers_nr_processed_homhap_other': papers_nr_processed_homhap_other,
               'datasets_nr_processed_het': datasets_nr_processed_het,
               'datasets_nr_processed_het_growth': datasets_nr_processed_het_growth,
               'datasets_nr_processed_het_expression': datasets_nr_processed_het_expression,
               'datasets_nr_processed_het_other': datasets_nr_processed_het_other,
               'papers_nr_processed_het': papers_nr_processed_het,
               'papers_nr_processed_het_growth': papers_nr_processed_het_growth,
               'papers_nr_processed_het_expression': papers_nr_processed_het_expression,
               'papers_nr_processed_het_other': papers_nr_processed_het_other,
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
