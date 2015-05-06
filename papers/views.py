from django.views import generic
from django.views.generic.base import TemplateView
from django.db.models import Q, Count
import json


from papers.models import Paper


class PaperIndexView(generic.ListView):
    model = Paper
    template_name = 'papers/index.html'
    context_object_name = 'papers_list'

    def get_context_data(self, **kwargs):
        context = super(PaperIndexView, self).get_context_data(**kwargs)
        context['num_all'] = Paper.objects.count()
        context['num_haploid'] = Paper.objects.filter(dataset__collection__ploidy=1).distinct().count()
        context['num_diploid_homozygous'] = Paper.objects.filter(dataset__collection__shortname='hom').distinct().count()
        context['num_diploid_heterozygous'] = Paper.objects.filter(dataset__collection__shortname='het').distinct().count()
        context['num_quantitative'] = Paper.objects.filter(dataset__data_available='quantitative').distinct().count()
        context['num_discrete'] = Paper.objects.filter(dataset__data_available='discrete').distinct().count()
        return context


class PaperAllIndexView(PaperIndexView):
    queryset = Paper.objects.order_by('pmid')

    def get_context_data(self, **kwargs):
        context = super(PaperAllIndexView, self).get_context_data(**kwargs)
        context['sub_navigation'] = 'All'
        return context


class PaperHaploidIndexView(PaperIndexView):
    queryset = Paper.objects.filter(dataset__collection__ploidy=1).distinct().order_by('pub_date')

    def get_context_data(self, **kwargs):
        context = super(PaperHaploidIndexView, self).get_context_data(**kwargs)
        context['sub_navigation'] = 'Haploid'
        return context


class PaperDiploidHomozygousIndexView(PaperIndexView):
    queryset = Paper.objects.filter(dataset__collection__shortname='hom').distinct().order_by('pub_date')

    def get_context_data(self, **kwargs):
        context = super(PaperDiploidHomozygousIndexView, self).get_context_data(**kwargs)
        context['sub_navigation'] = 'Diploid homozygous'
        return context


class PaperDiploidHeterozygousIndexView(PaperIndexView):
    queryset = Paper.objects.filter(dataset__collection__shortname='het').distinct().order_by('pub_date')

    def get_context_data(self, **kwargs):
        context = super(PaperDiploidHeterozygousIndexView, self).get_context_data(**kwargs)
        context['sub_navigation'] = 'Diploid heterozygous'
        return context


class PaperQuantitativeIndexView(PaperIndexView):
    queryset = Paper.objects.filter(dataset__data_available='quantitative').distinct().order_by('pub_date')

    def get_context_data(self, **kwargs):
        context = super(PaperQuantitativeIndexView, self).get_context_data(**kwargs)
        context['sub_navigation'] = 'Quantitative'
        return context

class PaperDiscreteIndexView(PaperIndexView):
    queryset = Paper.objects.filter(dataset__data_available='discrete').distinct().order_by('pub_date')

    def get_context_data(self, **kwargs):
        context = super(PaperDiscreteIndexView, self).get_context_data(**kwargs)
        context['sub_navigation'] = 'Discrete'
        return context


class PaperDetailView(generic.DetailView):
    model = Paper
    template_name = 'papers/detail.html'


class ContributorsListView(generic.ListView):
    model = Paper
    template_name = 'papers/contributors.html'
    context_object_name = 'papers_list'

    def get_queryset(self):
        return Paper.objects.filter(
            Q(dataset__data_source__acknowledge=True) | Q(dataset__tested_source__acknowledge=True)).distinct()
