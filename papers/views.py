from django.db.models import Q
from django.views import generic
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from papers.models import Paper

from Bio import Entrez

import os
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404
from django.conf import settings


def paper_list_view(request):

    queryset = Paper.objects.all()

    # Exclude the papers marked as "not relevant"
    f = Q(data_statuses__name__exact='not relevant') | Q(tested_statuses__name__exact='not relevant')
    queryset = queryset.exclude(f)

    if 'q' in request.GET:
        q = request.GET['q'].strip()
        f = Q(first_author__icontains=q) | Q(last_author__icontains=q) | Q(pmid__contains=q)
        f = f | Q(dataset__phenotype__observable__name__icontains=q)
        f = f | Q(dataset__conditionset__conditions__type__name__icontains=q) | Q(dataset__conditionset__conditions__type__other_names__icontains=q)
        f = f | Q(dataset__conditionset__conditions__type__chebi_name__icontains=q)
        f = f | Q(dataset__conditionset__conditions__type__pubchem_name__icontains=q)
        f = f | Q(dataset__medium__conditions__type__name__icontains=q) | Q(dataset__medium__conditions__type__other_names__icontains=q)
        f = f | Q(dataset__medium__conditions__type__chebi_name__icontains=q)
        f = f | Q(dataset__medium__conditions__type__pubchem_name__icontains=q)
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

        context['DOWNLOAD_PREFIX'] = settings.DOWNLOAD_PREFIX
        context['USER_AUTH'] = self.request.user.is_authenticated()

        # Define dataset_set
        dataset_list = obj.dataset_set.select_related('phenotype__observable2').select_related('collection').select_related('conditionset').all()
        page = self.request.GET.get('page', 1)
        paginator = Paginator(dataset_list, 50)
        try:
            datasets = paginator.page(page)
        except PageNotAnInteger:
            datasets = paginator.page(1)
        except EmptyPage:
            datasets = paginator.page(paginator.num_pages)

        context['datasets'] = datasets

        context['id'] = obj.id

        # Give credit if credit is due.
        names = obj.acknowledgements_str_list()
        to_acknowledge = []
        if obj.acknowledge_data():
            to_acknowledge.append('the data')
        if obj.acknowledge_tested():
            to_acknowledge.append('the list of tested strains')

        if names:
            thanks = ' and '.join(to_acknowledge) + ' for this paper were kindly provided by ' + names + '.'
            context['thanks'] = thanks

        # Fetch article info from Pubmed
        if obj.pmid != 0:
            Entrez.email = 'abarysh@princeton.edu'
            handle = Entrez.efetch(db='pubmed', id=[str(obj.pmid)], retmode='xml')
            xml_data = Entrez.read(handle)
            article = xml_data.get('PubmedArticle')[0].get('MedlineCitation').get('Article')
            authors_list = [(u'%s %s' % (author['ForeName'], author['LastName'])) for author in article['AuthorList']]
            if 'Year' in article['Journal']['JournalIssue']['PubDate']:
                pubdate = article['Journal']['JournalIssue']['PubDate']['Year']
            elif 'MedlineDate' in article['Journal']['JournalIssue']['PubDate']:
                pubdate = article['Journal']['JournalIssue']['PubDate']['MedlineDate']
            else:
                pubdate = ''

            if 'Pagination' in article.keys():
                pgn = article['Pagination']['MedlinePgn']
            else:
                pgn = '.'

            if 'Volume' in article['Journal']['JournalIssue'].keys():
                vol = article['Journal']['JournalIssue']['Volume']
            else:
                vol = ''

            context['title'] = article['ArticleTitle']
            context['authors'] = authors_list
            context['abstract'] = article['Abstract']['AbstractText'][0]
            context['citation'] = u'%s %s; %s:%s' % (article['Journal']['ISOAbbreviation'],
                                                      pubdate,
                                                      vol,
                                                      pgn)

        return context


class ContributorsListView(generic.ListView):
    model = Paper
    template_name = 'papers/contributors.html'
    context_object_name = 'papers_list'

    def get_queryset(self):
        return Paper.objects.filter(
            Q(dataset__data_source__acknowledge=True) | Q(dataset__tested_source__acknowledge=True)).distinct()


def download_zip(request, paper_id, paper_pmid):

    p = get_object_or_404(Paper, pk=paper_id)

    # Check data & tested strains permission status
    permissions_data = list(set(p.dataset_set.all().values_list('data_source__release', flat=True)))
    permissions_tested = list(set(p.dataset_set.all().values_list('tested_source__release', flat=True)))

    if all(permissions_data) & all(permissions_tested):
        file_name = os.path.join(settings.DATA_DIR, '%d.zip' % p.pmid)
    else:
        file_name = os.path.join(settings.DATA_DIR, "na.zip")

    file_path = os.path.join(settings.STATIC_ROOT, file_name)

    response = HttpResponse(open(file_path, 'rb'), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s_%d.zip"' % (settings.DOWNLOAD_PREFIX, p.pmid)
    return response


def paper_datasets(request, paper_id):
    p = get_object_or_404(Paper, pk=paper_id)

    txt = '\n'.join([(u'%s\t%s' % (d.id, d.name)) for d in p.dataset_set.all()])

    response = HttpResponse(txt, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="%s_%d_datasets_list.txt"' % (settings.DOWNLOAD_PREFIX, p.pmid)

    return response



