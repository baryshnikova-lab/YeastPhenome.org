from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.contrib.auth.decorators import login_required

from papers.models import Paper
from datasets.models import Dataset, Data
from conditions.models import ConditionType

from libchebipy import ChebiEntity


@login_required
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
    response['Content-Disposition'] = 'attachment; filename="%s_%s:%s_data.txt"' % (settings.DOWNLOAD_PREFIX, domain, id)

    return response