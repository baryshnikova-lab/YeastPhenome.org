from django.db.models import Q,Count
from django.views import generic
from django.views.generic.base import TemplateView
from django.http.request import QueryDict

from papers.models import Paper
import operator

# These only needed for zipo
from django.http import HttpResponse,Http404
from django.shortcuts import get_object_or_404
import os
from cStringIO import StringIO
from zipfile import ZipFile



class PaperIndexView(generic.ListView):
    model = Paper
    template_name = 'papers/index.html'
    context_object_name = 'papers_list'
    the_filter = Q()
    GOT=False

    @classmethod
    def filtered_count(cls,qs,got):
        # Filter queryset through the_filter of this object and return
        # how many we have
        return qs.filter(cls.get_filter(got)).distinct().count()

    @classmethod
    def _get_get(cls,got,key,query=lambda k,v: [Q(**{'%s__contains'%(k):v})]):
        items = got.getlist(key)
        q=[]

        if 0 != len(items):
            for item in items:
                item=item.strip()
                q.extend(query(key,item))
        if 0 != len(q):
            return reduce(operator.or_,q)
        return Q()

    @classmethod
    def get_filter(cls,got):
        q=[cls.the_filter]

        q.append(cls._get_get(got,'pmid'))
        q.append(cls._get_get(got,'author',
                              query=lambda k,v:[Q(first_author__contains=v),Q(last_author__contains=v)]
                          ))

        if 0 != len(q):
            return reduce(operator.and_,q)
        return cls.the_filter

    def get_queryset(self):
        # Returns the abjects fistered with get_filter.
        return Paper.objects.filter(self.get_filter(self.scrub_GET())).distinct()

    def scrub_GET(self):
        if self.GOT:
            return self.GOT

        OUT=QueryDict(mutable=True)

        # their can only be one 'debug' items and it must equal an
        # integer.
        if 'debug' in self.request.GET:
            raw=self.request.GET['debug'].strip()
            if raw.isdigit():
                # it's now scrubbed
                OUT['debug']=raw


        # their can be multiple pmid entries, all integers
        if 'pmid' in self.request.GET:
            scrubbed_pmids=[]
            raw_pmids=self.request.GET.getlist('pmid')
            for pmid in raw_pmids:
                pmid=pmid.strip()
                if pmid.isdigit():
                    scrubbed_pmids.append(pmid)
                if 0 != len(scrubbed_pmids):
                    OUT.setlist('pmid',set(scrubbed_pmids))

        # their can be more then one author.  Probably should only
        # accetp word characters and whitespace but for naw anything
        # goes.
        if 'author' in self.request.GET:
            scrubbed_authors=[]
            raw_authors=self.request.GET.getlist('author')
            for author in raw_authors:
                author=author.strip()
                if 0 != len(author):
                    scrubbed_authors.append(author)
            if 0 != len(scrubbed_authors):
                OUT.setlist('author',set(scrubbed_authors))

        #print OUT
        self.GOT=OUT
        return OUT

    def get_context_data(self, **kwargs):
        context = super(PaperIndexView, self).get_context_data(**kwargs)
        got=self.scrub_GET()
        qs=Paper.objects.filter(PaperAllIndexView.get_filter(got))

        context['debug']=got.get('debug')
        context['got'] = '?%s' % (got.urlencode())
        if '?' == context['got']:
            context['got'] = ''

        context['num_all'] = qs.count()

        # Sure, the filter is still specified in two places, but at
        # least now the two places are right next to each other
        context['num_haploid'] = PaperHaploidIndexView.filtered_count(qs,got)
        context['num_diploid_homozygous'] = PaperDiploidHomozygousIndexView.filtered_count(qs,got)
        context['num_diploid_heterozygous'] = PaperDiploidHeterozygousIndexView.filtered_count(qs,got)
        context['num_quantitative'] = PaperQuantitativeIndexView.filtered_count(qs,got)
        context['num_discrete'] = PaperDiscreteIndexView.filtered_count(qs,got)

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


def zipo(request,paper_id):
    p = get_object_or_404(Paper,pk=paper_id)
    if not(p.has_data()):
        raise Http404("Paper has no data.");

    zip_buff=StringIO()
    zip_file=ZipFile(zip_buff,'w')

    dp=p.download_path()
    for root,_,basenames in os.walk(dp):
        for name in basenames:
            path=os.path.join(root,name)
            an=path.replace(dp,'')
            zip_file.write(path,arcname=an)
    zip_file.close()

    return HttpResponse(zip_buff.getvalue(),content_type="application/zip")
