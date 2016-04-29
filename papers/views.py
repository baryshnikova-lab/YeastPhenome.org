from django.db.models import Q
from django.views import generic
from django.shortcuts import render

from papers.models import Paper
import urllib2, re

# These only needed for zipo
import os
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.conf import settings
from cStringIO import StringIO
from zipfile import ZipFile


def paper_list_view(request):

    queryset = Paper.objects.all()

    # Exclude the papers marked as "not relevant"
    f = Q(data_statuses__status_name__exact='not relevant') | Q(tested_statuses__status_name__exact='not relevant')
    queryset = queryset.exclude(f)

    if 'q' in request.GET:
        q = request.GET['q']
        f = Q(first_author__icontains=q) | Q(last_author__icontains=q) | Q(pmid__contains=q)
        f = f | Q(dataset__phenotype__observable2__name__icontains=q)
        f = f | Q(dataset__conditionset__conditions__type__name__icontains=q) | Q(dataset__conditionset__conditions__type__short_name__icontains=q)
        queryset = queryset.filter(f)
    else:
        q = ''

    queryset = queryset.distinct().order_by('pmid')

    return render(request, 'papers/index.html', {
        'papers_list': queryset,
        'q': q,
    })


class PaperDetailView(generic.DetailView):
    model = Paper
    template_name = 'papers/detail.html'

    def get_context_data(self, **kwargs):
        context = super(PaperDetailView, self).get_context_data(**kwargs)
        obj = context['object']

        # Give credit if where credit is due.
        names = obj.sources_to_acknowledge()
        if names:
            gd = obj.got_data()
            gt = obj.got_tested()

            thanks = False
            if gd:
                if gt:
                    thanks = 'The data and the list of tested genes for this publication were kindly provided by <b>%s</b>.'
                else:
                    thanks = 'The data for this publication was kindly provided by <b>%s</b>.'
                thanks = thanks + '<br>The data contains unpublished values and is more complete than its published version. However, it may contain false positives and thus should be handled with care.'
            elif gt:
                thanks = 'The list of tested genes for this publication was kindly provided by <b>%s</b>.'
            if thanks:
                context['thanks'] = thanks % names
        # Credit now given

        # Fetch PMID info if we have to
        pmid = obj.pmid
        if pmid == 0:
            # If we have no PMID just bail
            return context
        ml = os.path.join(settings.MEDLINE_DIR, "%s.txt" % (pmid))
        if os.path.isfile(ml):
            pass
        else:
            try:
                out = open(ml, 'w')
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

    rm=settings.README
    if rm and os.path.isfile(rm):
        zip_file.write(rm,os.path.basename(rm))

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
