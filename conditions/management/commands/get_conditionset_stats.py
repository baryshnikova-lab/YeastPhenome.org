from django.core.management.base import BaseCommand
from django.db.models import Q, F, Count, Sum, Case, When

from conditions.models import ConditionSet
from datasets.models import Dataset
from papers.models import Paper


class Command(BaseCommand):

    def handle(self, *args, **options):

        conditionsets_qs = ConditionSet.objects.all()

        # Total number
        conditionset_nr = conditionsets_qs.count()
        self.stdout.write('Total: %s.' % conditionset_nr)

        # Those associated with a loaded paper
        f1 = Q(dataset__paper__latest_data_status__status__name='loaded')
        conditionset_nr = conditionsets_qs.filter(f1).distinct().count()
        self.stdout.write('Loaded: %s.' % conditionset_nr)

        # Those associated with growth
        f2 = Q(dataset__phenotype__observable__name='growth')
        conditionset_nr = conditionsets_qs.filter(f1).filter(f2).distinct().count()
        self.stdout.write('Loaded + growth: %s.' % conditionset_nr)

        # Those that are chemicals
        f3 = Q(conditions__type__tags__name='chemical')
        conditionset_nr = conditionsets_qs.filter(f1).filter(f2).filter(f3).distinct().count()
        self.stdout.write('Loaded + growth + chemical: %s.' % conditionset_nr)


