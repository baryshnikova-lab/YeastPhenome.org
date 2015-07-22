from django.db.models import Q,Count
from django.views import generic
from django.views.generic.base import TemplateView
from django.http.request import QueryDict

from papers.models import Paper
import operator

from phenotypes.models import Observable2
from conditions.models import ConditionType

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

    the_filter = Q() # this should be overloaded
    queryset = Paper.objects.filter(the_filter).distinct().order_by('pub_date')

    GOT = False # for caching multiple requests
    template_ref = None # for tweaking with the template

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
            # sometimes we don't
            out=set(list(Paper.objects.filter(cls.get_filter(got)).distinct()))

        # we have already filtered by PMID, so lets get rid of the numbers.
        words=[]
        for item in got.getlist('s'):
            if not(item.isdigit()):
                words.append(item)

        # If there is nothing else to search for we can bail now.
        if 0 == len(words):
            return out

        # logical or all the words together
        q=[]
        for word in words:
            q.append(Q(name__contains=word))
        # we want to search the name column in both Observable2 and
        # ConditionsType

        # now we get phenotypes
        os=Observable2.objects.filter(reduce(operator.or_,q))
        for o in os:
            # filter out papers not of out type
            out=out.union(o.paper_list().filter(cls.the_filter))

        # in the conditionType search we also want to check the
        # "short_name" column.
        for word in words:
            q.append(Q(short_name__contains=word))

        # here we get conditions
        cs=ConditionType.objects.filter(reduce(operator.or_,q))
        for c in cs:
            out=out.union(c.paper_list().filter(cls.the_filter))

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

    @classmethod
    def scrub_GET_txt(self,get):
        """Returns text suitable for putting in the search box."""
        return self.got_txt(self.scrub_GET(get))

    @classmethod
    def got_txt(self,got):
        """Same as scrub_GET_txt() but assume got is already scrubbed."""
        return ' '.join(got.getlist('s'))

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

    @classmethod
    def context_update(cls,self_,qs,got):
        out={}
        key='num_%s' % (cls.template_ref)

        if type(self_) == cls:
            out[key]=len(qs)
            #out[key]=cls.filtered_count(got)
            out['sub_navigation']=cls.template_ref.replace('_',' ').capitalize()
        else:
            out[key]=cls.filtered_count(got)
        return out

    def get_context_data(self, **kwargs):
        """Message the default context data to something we can use."""

        context = super(PaperIndexView, self).get_context_data(**kwargs)
        got=self._scrub_GET()

        # filter out by pmid and author
        papers=context['papers_list']

        papers=self.filtered_list(got,qs=papers)
        # at this pount papers is a list, no a QuerySet.

        context['s']=self.got_txt(got)
        context['papers_list']=papers
        context['verbose']=got.get('verbose')
        context['got'] = '?%s' % (got.urlencode())
        if '?' == context['got']:
            context['got'] = ''

        # Let get totals for each paper type
        context.update(PaperAllIndexView.context_update
                       (self,papers,got))
        context.update(PaperHaploidIndexView.context_update
                       (self,papers,got))
        context.update(PaperDiploidHomozygousIndexView.context_update
                       (self,papers,got))
        context.update(PaperDiploidHeterozygousIndexView.context_update
                       (self,papers,got))
        context.update(PaperQuantitativeIndexView.context_update
                       (self,papers,got))
        context.update(PaperDiscreteIndexView.context_update
                       (self,papers,got))

        return context


class PaperAllIndexView(PaperIndexView):
    queryset = Paper.objects.order_by('pmid')
    template_ref = 'all'

class PaperHaploidIndexView(PaperIndexView):
    the_filter = Q(dataset__collection__ploidy=1)
    template_ref = 'haploid'

class PaperDiploidHomozygousIndexView(PaperIndexView):
    the_filter = Q(dataset__collection__shortname='hom')
    template_ref = 'diploid_homozygous'

class PaperDiploidHeterozygousIndexView(PaperIndexView):
    the_filter = Q(dataset__collection__shortname='het')
    template_ref='diploid_heterozygous'

class PaperQuantitativeIndexView(PaperIndexView):
    the_filter = Q(dataset__data_available='quantitative')
    template_ref='quantitative'

class PaperDiscreteIndexView(PaperIndexView):
    the_filter = Q(dataset__data_available='discrete')
    template_ref='discrete'

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
