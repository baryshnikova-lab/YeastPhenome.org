from django.shortcuts import get_object_or_404, render
from django.db.models import Count, Sum

from papers.models import Paper, ConditionType, Condition, ConditionSet, Observable2, Data
from papers.views import PaperIndexView

def index(request):
    paper_num_total = Paper.objects.all().count()
    paper_num_with_data = Data.objects.values('dataset__paper').distinct().count()
    phenotype_num_total = Observable2.objects.exclude(phenotype__dataset = None).count()
    phenotype_num_with_data = Data.objects.values('dataset__phenotype__observable2__name').distinct().count()
    condition_num = Condition.objects.all().count()
    latest_paper = Paper.objects.all().latest().modified_on
    latest_condition = Condition.objects.all().latest().modified_on

    most_studied_phenotype = Observable2.objects.annotate(num_datapoints=Sum('phenotype__dataset__tested_num')).order_by('-num_datapoints').first()
    most_studied_conditionset = ConditionSet.objects.exclude(name='standard').exclude(name='').values('name').annotate(num_datapoints=Sum('dataset__tested_num')).order_by('-num_datapoints').first()

    context = {'paper_num_total': paper_num_total, 'paper_num_with_data': paper_num_with_data,
               'phenotype_num_total': phenotype_num_total, 'phenotype_num_with_data': phenotype_num_with_data,
               'condition_num': condition_num,
               'most_studied_conditionset': most_studied_conditionset,
               'most_studied_phenotype': most_studied_phenotype,
               'updated': max(latest_paper, latest_condition),

               # To repopulate the search box
               's':PaperIndexView.scrub_GET_txt(request.GET)
               }
    return render(request, 'yeastphenome/index.html', context)
