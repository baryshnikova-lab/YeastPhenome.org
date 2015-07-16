from django.db.models import Q,Count
from django.views import generic
from django.views.generic.base import TemplateView
from django.http.request import QueryDict

from papers.models import Paper
import operator

from phenotypes.models import Observable2

# These only needed for zipo
import os
from django.http import HttpResponse,Http404
from django.shortcuts import get_object_or_404
from django.conf import settings
from cStringIO import StringIO
from zipfile import ZipFile



class PaperIndexView(generic.ListView):
    """A virtual class."""

    model = Paper
    template_name = 'papers/index.html'
    context_object_name = 'papers_list'
    the_filter = Q()
    GOT=False

    @classmethod
    def filtered_count(cls,got):
        """Filter queryset through the_filter of this object and return how many we have."""
        return len(cls.filtered_list(got))

    @classmethod
    def filtered_list(cls,got,qs=False):
        """Returns a list of papers that match the query.  We assume got
        argument is already scrubbed."""

        out=None
        if qs:
            # Sometimes we already have the first bit of the query, we
            # don't need to redo it.
            out=set(list(qs.filter(cls.get_filter(got)).distinct()))
        else:
            out=set(list(Paper.objects.filter(cls.get_filter(got)).distinct()))

        # we have already filtered by PMID, so lets get rid of the numbers.
        words=[]
        for item in got.getlist('s'):
            if not(item.isdigit()):
                words.append(item)

        # If there is nothing else to search for we can bail now.
        if 0 == len(words):
            return out

        # or all the words together
        q=[]
        for word in words:
            q.append(Q(name__contains=word))
        os=Observable2.objects.filter(reduce(operator.or_,q))

        for o in os:
            # filter out papers not of out type
            out=out.union(o.paper_list().filter(cls.the_filter))

        return out

    @classmethod
    def get_filter(cls,got):
        """Returns a filter for the query specified in the, already scrubbed,
        got variable."""

        q=[]

        if 's' in got:
            # we assume already scrubbed
            esses=got.getlist('s')
            for s in esses:
                if s.isdigit():
                    q.append(Q(pmid__contains=s))
                else:
                    q.extend([Q(first_author__contains=s),Q(last_author__contains=s)])

        # Now we want to OR everything in q, then and it with
        # qs.the_filter, but we don't want to do more then we need.

        if 1 == len(q):
            return reduce(operator.and_,[cls.the_filter,q[0]])
        elif 1 < len(q):
            return reduce(operator.and_,[cls.the_filter,reduce(operator.or_,q)])
        return cls.the_filter # if 0==len(q)

    def get_queryset(self):
        """Returns the Paper.objects filtered with get_filter and self.request.GET."""
        return Paper.objects.filter(self.get_filter(self._scrub_GET())).distinct()

    def _scrub_GET(self):
        """Returns a scrubbed self.request.GET"""
        if not(self.GOT):
            self.GOT=self.scrub_GET(self.request.GET)
        return self.GOT

    @classmethod
    def scrub_GET(self,GET):
        "Scrubbs a QueryDict object."
        OUT=QueryDict(mutable=True)

        # their can only be one 'debug' items and it must equal an
        # integer.
        if 'verbose' in GET:
            raw=GET['verbose'].strip()
            if raw.isdigit():
                # it's now scrubbed
                OUT['verbose']=raw

        # multilpe 's' get split by white space as well
        if 's' in GET:
            esses = GET.getlist('s')
            s=[]
            for ess in esses:
                s.extend(ess.strip().split())
            OUT.setlist('s',s)

        # anything else is hacking.
        return OUT

    def get_context_data(self, **kwargs):
        """Message the default context data to something we can use."""

        context = super(PaperIndexView, self).get_context_data(**kwargs)
        got=self._scrub_GET()

        # filter out by pmid and author
        qs=context['papers_list']

        # Get the rest of the papers
        papers=self.filtered_list(got,qs=qs)
        context['papers_list']=papers

        context['verbose']=got.get('verbose')
        context['got'] = '?%s' % (got.urlencode())
        if '?' == context['got']:
            context['got'] = ''

        context['num_all'] = PaperAllIndexView.filtered_count(got)

        # Sure, the filter is still specified in two places, but at
        # least now the two places are right next to each other
        context['num_haploid'] = PaperHaploidIndexView.filtered_count(got)
        context['num_diploid_homozygous'] = PaperDiploidHomozygousIndexView.filtered_count(got)
        context['num_diploid_heterozygous'] = PaperDiploidHeterozygousIndexView.filtered_count(got)
        context['num_quantitative'] = PaperQuantitativeIndexView.filtered_count(got)
        context['num_discrete'] = PaperDiscreteIndexView.filtered_count(got)

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
    """Constructs a zip file in memory for users to download."""

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

    out=HttpResponse(zip_buff.getvalue(),content_type="application/zip")
    out['Content-Disposition'] = 'attachment; filename="%s_%d.zip"' % (settings.DOWNLOAD_PREFIX,p.pmid)
    return out
