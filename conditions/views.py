from django.views import generic
from django.views.generic.base import TemplateView
from django.db.models import Count
import json

from conditions.models import ConditionType


class ConditionIndexView(generic.ListView):
    model = ConditionType
    template_name = 'conditions/index.html'
    context_object_name = 'conditiontype_list'

    def get_queryset(self):
        return ConditionType.objects.order_by('name')


class ConditionGraphView(TemplateView):
    template_name = 'conditions/graph.html'

    def get_context_data(self, **kwargs):
        context = super(ConditionGraphView, self).get_context_data(**kwargs)
        data = [{
            'type':s.type,
            'name':s.name,
            'short_name':s.shortname,
            'size':s.num_datasets,
        } for s in ConditionType.objects.annotate(num_datasets=Count('condition__conditionset__dataset')).order_by('-num_datasets')]
        context['stats'] = json.dumps(data)
        return context


class ConditionDetailView(generic.DetailView):
    model = ConditionType
    template_name = 'conditions/detail.html'