from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.views import generic

from papers.models import Paper
from datasets.models import Dataset, Data
from conditions.models import ConditionType
from phenotypes.models import Observable2

from libchebipy import ChebiEntity


class DatasetDetailView(generic.DetailView):
    model = Dataset
    template_name = 'datasets/detail.html'
    context_object_name = 'dataset'


def index(request):

    context = ''
    return render(request, 'datasets/index.html', context)


def datasets_growth(request):

    class_description = 'List of datasets that measure growth in rich or minimal media. These may be standalone experiments or controls within larger studies of chemical and/or physical perturbations.'

    datasets = Dataset.objects.filter(conditionset__name='standard')\
        .filter(phenotype__observable2__name__startswith='growth')\
        .exclude(paper__latest_data_status__status__status_name='not relevant').distinct()
    return render(request, 'datasets/class.html', {
        'datasets': datasets,
        'class_description': class_description,
        'class_name': 'Growth in rich or minimal media',
        'DOWNLOAD_PREFIX': settings.DOWNLOAD_PREFIX,
        'USER_AUTH': request.user.is_authenticated()
    })


def download_all(request):

    datasets = Dataset.objects.\
        select_related('paper__latest_tested_status__status').\
        filter(paper__latest_data_status__status__status_name='loaded').all()

    datasets_list = list()
    for d in datasets:
        fields = [d.id, d.name, d.paper.pmid, d.paper.latest_tested_status]
        fields_str = '\t'.join(['%s' % field for field in fields])
        datasets_list.append(fields_str)
    txt = '\n'.join(datasets_list)

    txt = 'id\tname\tpmid\tlatest_tested_status\n' + txt

    response = HttpResponse(txt, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="%s_datasets.txt"' % settings.DOWNLOAD_PREFIX

    return response


def download(request):

    file_header = ''

    # datasets = []
    # for key, value in request.GET.iteritems():
    #     datasets.append(key)
    datasets = sorted(request.GET)

    data = Data.objects.filter(dataset_id__in=datasets).all()

    orfs = list(data.values_list('orf', flat=True).distinct())
    datasets_ids = list(data.values_list('dataset_id', flat=True).order_by('dataset__paper').distinct())
    matrix = [[None] * len(datasets_ids) for i in orfs]

    for datapoint in data:
        i = orfs.index(datapoint.orf)
        j = datasets_ids.index(datapoint.dataset_id)
        matrix[i][j] = datapoint.value

    column_headers = '\t' + '\t'.join(
        [u'%s' % get_object_or_404(Dataset, pk=dataset_id) for dataset_id in datasets_ids]) + '\n'

    data_row = []
    for i, orf in enumerate(orfs):
        new_row = orf + '\t' + '\t'.join([str(val) for val in matrix[i]])
        print(new_row)
        data_row.append(new_row)

    txt3 = '\n'.join(data_row)

    response = HttpResponse(file_header + column_headers + txt3, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="%s_data.txt"' % (settings.DOWNLOAD_PREFIX)

    return response


def data(request, domain, id):

    file_header = ''

    if domain == 'papers':
        paper = get_object_or_404(Paper, pk=id)
        datasets = paper.dataset_set
        file_header = u'# Paper: %s (PMID %s)\n' % (paper, paper.pmid)

    if domain == 'datasets':
        # datasets = get_object_or_404(Dataset, pk=id)
        datasets = Dataset.objects.filter(pk=id)
        dataset = datasets.first()
        file_header = u'# Paper: %s (PMID %s)\n# Dataset: %s\n' % (dataset.paper, dataset.paper.pmid, dataset)

    if domain == 'conditions':
        conditiontype = get_object_or_404(ConditionType, pk=id)
        datasets = conditiontype.datasets()
        file_header = u'# Condition: %s (ID %s)\n' % (conditiontype, conditiontype.id)

    if domain == 'chebi':
        chebi_entity = ChebiEntity('CHEBI:' + str(id))
        children = []
        for relation in chebi_entity.get_incomings():
            if relation.get_type() == 'has_role':
                tid = relation.get_target_chebi_id()
                tid = int(filter(str.isdigit, tid))
                children.append(tid)
        datasets = Dataset.objects.filter(conditionset__conditions__type__chebi_id__in=children)
        file_header = u'# Data for conditions annotated as %s (ChEBI:%s)\n' % (chebi_entity.get_name(), id)

    if domain == 'phenotypes':
        phenotype = get_object_or_404(Observable2, pk=id)
        datasets = phenotype.datasets()
        file_header = u'# Phenotype: %s (ID %s)\n' % (phenotype, phenotype.id)

    data = Data.objects.filter(dataset_id__in=datasets.values('id')).all()

    orfs = list(data.values_list('orf', flat=True).distinct())
    datasets_ids = list(data.values_list('dataset_id', flat=True).order_by('dataset__paper').distinct())
    matrix = [[None] * len(datasets_ids) for i in orfs]

    for datapoint in data:
        i = orfs.index(datapoint.orf)
        j = datasets_ids.index(datapoint.dataset_id)
        matrix[i][j] = datapoint.value

    column_headers = '\t' + '\t'.join(
        [u'%s' % get_object_or_404(Dataset, pk=dataset_id) for dataset_id in datasets_ids]) + '\n'

    data_row = []
    for i, orf in enumerate(orfs):
        new_row = orf + '\t' + '\t'.join([str(val) for val in matrix[i]])
        print(new_row)
        data_row.append(new_row)

    txt3 = '\n'.join(data_row)

    response = HttpResponse(file_header+column_headers+txt3, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="%s_%s_%s_data.txt"' % (settings.DOWNLOAD_PREFIX, domain, id)

    return response