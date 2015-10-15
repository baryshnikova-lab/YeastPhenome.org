from django.views import generic
from django.views.generic.base import TemplateView
from django.db.models import Count
from django.http import HttpResponse
import json

from .models import ConditionType


class ConditionIndexView(generic.ListView):
    model = ConditionType
    template_name = 'conditions/index.html'
    context_object_name = 'conditiontype_list'

    def get_queryset(self):
        return ConditionType.objects.order_by('name')

class ConditionDetailView(generic.DetailView):
    model = ConditionType
    template_name = 'conditions/detail.html'

class CirclePacking(generic.ListView):
    model = ConditionType
    template_name = 'conditions/circle.html'

    def flare(self,ctl):
        out={'name':'flare','children':[]}
        for ct in ctl:
            paper_count=len(ct.paper_list())
            if 0<paper_count:
                out['children'].append({
                    'name':ct.must_display_name(),
                    'size':paper_count
                })
        return out

    def get_context_data(self,**kwargs):
        context = super(generic.ListView,self).get_context_data(**kwargs)
        context['flare'] = json.dumps(self.flare(context['conditiontype_list']))
        return context
