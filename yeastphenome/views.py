from django.shortcuts import get_object_or_404, render
from django.db.models import Count, Sum

from papers.models import Paper, Data
from conditions.models import Condition, ConditionSet
from phenotypes.models import Observable2
from papers.views import PaperIndexView

import datetime


def index(request):
    latest_paper = Paper.objects.all().latest().modified_on
    latest_condition = Condition.objects.all().latest().modified_on

    if latest_condition is None:
        # fudging NULL entries in the database
        latest_condition = datetime.date(1,1,1)

    context = {
        'paper_num_total': Paper.objects.all().count(),
        'phenotype_num_total': Observable2.objects.exclude(phenotype__dataset = None).count(),
        'condition_num': Condition.objects.all().count(),
        'updated': max(latest_paper, latest_condition),

        # To repopulate the search box
        's':PaperIndexView.scrub_GET_txt(request.GET),
    }

    if 'verbose' in request.GET:
        context.update(
            {
                'paper_num_with_data': Data.objects.values('dataset__paper').distinct().count(),
                'phenotype_num_with_data': Data.objects.values('dataset__phenotype__observable2__name').distinct().count(),
                'most_studied_conditionset': ConditionSet.objects.exclude(name='standard').exclude(name='').values('name').annotate(num_datapoints=Sum('dataset__tested_num')).order_by('-num_datapoints').first(),
                'most_studied_phenotype':  Observable2.objects.annotate(num_datapoints=Sum('phenotype__dataset__tested_num')).exclude(num_datapoints=None).order_by('-num_datapoints').first(),
            }
        )
    return render(request, 'yeastphenome/index.html', context)

def about(request):
    """Really just to have access to the dynamic template."""
    return render(request, 'yeastphenome/about.html')
