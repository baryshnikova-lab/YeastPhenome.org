from django.core.management.base import BaseCommand
from django.db.models import Q, F, Count, Sum, Case, When

from conditions.models import ConditionType
from datasets.models import Dataset
from papers.models import Paper


class Command(BaseCommand):

    def handle(self, *args, **options):

        conditiontypes_qs = ConditionType.objects.all()

        # Total number
        conditiontype_nr = conditiontypes_qs.count()
        self.stdout.write('Total: %s.' % conditiontype_nr)

        # Those associated with a loaded paper
        f1 = Q(condition__conditionset__dataset__paper__latest_data_status__status__name='loaded')
        conditiontype_nr = conditiontypes_qs.filter(f1).distinct().count()
        self.stdout.write('Loaded: %s.' % conditiontype_nr)

        # Those associated with growth
        f2 = Q(condition__conditionset__dataset__phenotype__observable__name='growth')
        conditiontype_nr = conditiontypes_qs.filter(f1).filter(f2).distinct().count()
        self.stdout.write('Loaded + growth: %s.' % conditiontype_nr)

        # Those that are chemicals
        f3 = Q(tags__name='chemical')
        conditiontype_nr = conditiontypes_qs.filter(f1).filter(f2).filter(f3).distinct().count()
        self.stdout.write('Loaded + growth + chemical: %s.' % conditiontype_nr)

latest