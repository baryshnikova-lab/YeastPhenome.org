from django.views import generic
from django.views.generic.base import TemplateView
from django.db.models import Q,Count
from papers.models import Paper

import operator


class PaperIndexView(generic.ListView):
    model = Paper
    template_name = 'papers/index.html'
    context_object_name = 'papers_list'
    the_filter = Q()

    @classmethod
    def filtered_count(cls,qs,request):
        # Filter queryset through the_filter of this object and return
        # how many we have
        return qs.filter(cls.get_filter(request)).distinct().count()

    @classmethod
    def get_filter(cls,request):
        # Get the_filter anded with any requests made.  Currently only pmid.
        pmids=request.GET.getlist('pmid')

        # If a pmid was asked for
        if 0 != len(pmids):
            q=[]
            for pmid in pmids:
                pmid=pmid.strip()
                if pmid.isdigit():
                    # Only look for pmids that are all digits
                    q.append( Q(pmid__contains=pmid) )
            if 0 != len (q):
                return reduce(operator.and_,[reduce(operator.or_,q),cls.the_filter])
        return cls.the_filter

    def get_queryset(self):
        # Returns the abjects fistered with get_filter.
        return Paper.objects.filter(self.get_filter(self.request)).distinct()

    def get_context_data(self, **kwargs):
        context = super(PaperIndexView, self).get_context_data(**kwargs)
        qs=Paper.objects.filter(PaperAllIndexView.get_filter(self.request))

        # If we have a query string we need to pass that to the tab
        context['got'] = '?%s' % (self.request.GET.urlencode())
        if '?' == context['got']:
            context['got'] = ''

        context['num_all'] = qs.count()

        # Sure, the filter is still specified in two places, but at
        # least now the two places are right next to each other
        context['num_haploid'] = PaperHaploidIndexView.filtered_count(qs,self.request)
        context['num_diploid_homozygous'] = PaperDiploidHomozygousIndexView.filtered_count(qs,self.request)
        context['num_diploid_heterozygous'] = PaperDiploidHeterozygousIndexView.filtered_count(qs,self.request)
        context['num_quantitative'] = PaperQuantitativeIndexView.filtered_count(qs,self.request)
        context['num_discrete'] = PaperDiscreteIndexView.filtered_count(qs,self.request)

        return context


class PaperAllIndexView(PaperIndexView):
    queryset = Paper.objects.order_by('pmid')

    def get_context_data(self, **kwargs):
        context = super(PaperAllIndexView, self).get_context_data(**kwargs)
        context['sub_navigation'] = 'All'
        return context


class PaperHaploidIndexView(PaperIndexView):
    queryset = Paper.objects.filter(dataset__collection__ploidy=1).distinct().order_by('pub_date')
    the_filter = Q(dataset__collection__ploidy=1)

    def get_context_data(self, **kwargs):
        context = super(PaperHaploidIndexView, self).get_context_data(**kwargs)
        context['sub_navigation'] = 'Haploid'
        return context


class PaperDiploidHomozygousIndexView(PaperIndexView):
    queryset = Paper.objects.filter(dataset__collection__shortname='hom').distinct().order_by('pub_date')
    the_filter = Q(dataset__collection__shortname='hom')

    def get_context_data(self, **kwargs):
        context = super(PaperDiploidHomozygousIndexView, self).get_context_data(**kwargs)
        context['sub_navigation'] = 'Diploid homozygous'
        return context


class PaperDiploidHeterozygousIndexView(PaperIndexView):
    queryset = Paper.objects.filter(dataset__collection__shortname='het').distinct().order_by('pub_date')
    the_filter = Q(dataset__collection__shortname='het')

    def get_context_data(self, **kwargs):
        context = super(PaperDiploidHeterozygousIndexView, self).get_context_data(**kwargs)
        context['sub_navigation'] = 'Diploid heterozygous'
        return context


class PaperQuantitativeIndexView(PaperIndexView):
    queryset = Paper.objects.filter(dataset__data_available='quantitative').distinct().order_by('pub_date')
    the_filter = Q(dataset__data_available='quantitative')

    def get_context_data(self, **kwargs):
        context = super(PaperQuantitativeIndexView, self).get_context_data(**kwargs)
        context['sub_navigation'] = 'Quantitative'
        return context

class PaperDiscreteIndexView(PaperIndexView):
    queryset = Paper.objects.filter(dataset__data_available='discrete').distinct().order_by('pub_date')
    the_filter = Q(dataset__data_available='discrete')

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
