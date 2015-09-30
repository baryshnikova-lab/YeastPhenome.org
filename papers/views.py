from django.db.models import Q,Count
from django.views import generic
from django.views.generic.base import TemplateView
from django.http.request import QueryDict

from papers.models import Paper
import operator
import urllib2,re

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

    the_filter = False # this should be overloaded
    GOT = False # for caching multiple requests
    template_ref = None # for tweaking with the template

    def get_queryset(self):

        got=self.scrub_GET()
        if 's' in got:
            papers=[] # hold list of paper ids

            for s in got.getlist('s'):
                o2s=Observable2.objects.filter(name__icontains=s)
                cts=ConditionType.objects.filter(
                    Q(name__icontains=s)|Q(short_name__icontains=s))

                ps=set()
                for o2 in o2s:
                    for paper in o2.paper_list():
                        ps.add(paper.id)
                for ct in cts:
                    for paper in ct.paper_list():
                        ps.add(paper.id)

                f=None
                if s.isdigit():
                    # we don't need to check PMID unless it's all digits
                    f=(Q(first_author__icontains=s)|Q(last_author__icontains=s)|
                       Q(pmid__contains=s)) # on icontains for PMID, it's a number
                else:
                    f=Q(first_author__icontains=s)|Q(last_author__icontains=s)

                for paper in Paper.objects.exclude(pk__in=ps).filter(f):
                    ps.add(paper.id)

                papers.append(ps)

            if 0 == len(papers):
                return []
            else:
                # We want to return a ResultSet because we need to
                # filter it again later.
                return Paper.objects.filter(pk__in=set.intersection(*papers))

        # if no query return everything
        return super(PaperIndexView, self).get_queryset()


    @classmethod
    def scrub_GET_txt(self,get):
        """Returns text suitable for putting in the search box."""
        return self.got_txt(self._scrub_GET(get))

    @classmethod
    def got_txt(self,got):
        """Same as scrub_GET_txt() but assume got is already scrubbed."""
        return ' '.join(got.getlist('s'))

    def scrub_GET(self):
        """Returns a scrubbed self.request.GET, scrub it if we haven't done so
        yet."""
        if not(self.GOT):
            self.GOT=self._scrub_GET(self.request.GET)
        return self.GOT

    @classmethod
    def _scrub_GET(self,GET):
        """Scrubbs a QueryDict object.  This function is subject to change
        without notice."""
        OUT=QueryDict(mutable=True)

        # multilpe 's' get split by white space as well
        if 's' in GET:
            esses = GET.getlist('s')
            s=[]
            for ess in esses:
                s.extend(ess.strip().split())
            if 0 < len(s):
                OUT.setlist('s',s)

        # anything else is hacking.
        return OUT

    @classmethod
    def context_update(cls,self_,qs,got):
        out={}
        key='num_%s' % (cls.template_ref)

        if type(self_) == cls:
            if cls.the_filter:
                qs=qs.filter(cls.the_filter).distinct().\
                    order_by('pub_date','pmid')
                out['papers_list']=qs
            out[key]=len(qs) # qs.count()
            out['sub_navigation']=cls.template_ref.replace('_',' ').capitalize()
        else:
            if cls.the_filter:
                out[key]=qs.filter(cls.the_filter).distinct().count()
            else:
                out[key]=len(qs)
        return out

    def get_context_data(self, **kwargs):
        """Message the default context data to something we can use."""

        context = super(PaperIndexView, self).get_context_data(**kwargs)
        got=self.scrub_GET()

        # filter out by pmid and author
        papers=context['papers_list']
        # Every thing is papers is in the results, now we need to
        # check everything else.  Bleck.

        context['s']=self.got_txt(got)
        context['got'] = '?%s' % (got.urlencode())
        if '?' == context['got']:
            context['got'] = ''

        # # Let get totals for each paper type
        # context.update(PaperAllIndexView.context_update
        #                (self,papers,got))
        # context.update(PaperHaploidIndexView.context_update
        #                (self,papers,got))
        # context.update(PaperDiploidHomozygousIndexView.context_update
        #                (self,papers,got))
        # context.update(PaperDiploidHeterozygousIndexView.context_update
        #                (self,papers,got))
        # context.update(PaperQuantitativeIndexView.context_update
        #                (self,papers,got))
        # context.update(PaperDiscreteIndexView.context_update
        #                (self,papers,got))

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

    def get_context_data(self,**kwargs):
        context=super(PaperDetailView,self).get_context_data(**kwargs)
        pmid = context['object'].pmid
        ml = os.path.join(settings.MEDLINE_DIR, "%s.txt" % (pmid))
        if os.path.isfile(ml):
            pass
        else:
            try:
                out = open(ml,'w')
                url = "https://www.ncbi.nlm.nih.gov/pubmed/%s?report=medline&format=text" % (pmid)
                r = urllib2.urlopen(url)
                out.write(re.sub('<[^<]+?>', '', r.read()).strip())
                out.close()
            except IOError:
                pass
        return context


class ContributorsListView(generic.ListView):
    model = Paper
    template_name = 'papers/contributors.html'
    context_object_name = 'papers_list'

    def get_queryset(self):
        return Paper.objects.filter(
            Q(dataset__data_source__acknowledge=True) | Q(dataset__tested_source__acknowledge=True)).distinct()


def zipo(request,pk):
    """Constructs a zip file in memory for users to download."""

    p = get_object_or_404(Paper,pk=pk)
    if not(p.should_have_data()):
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
