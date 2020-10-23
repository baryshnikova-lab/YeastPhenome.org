from django.core.management.base import BaseCommand
from django.db.models import Q, F, Count, Sum, Case, When, Min, Max
from django.db.models.functions import Concat

import numpy as np

from datasets.models import Dataset
from papers.models import Paper
from phenotypes.models import Phenotype, Observable


class Command(BaseCommand):

    def handle(self, *args, **options):

        datasets_qs = Dataset.objects.all()
        papers_qs = Paper.objects.all()

        # Papers processed and loaded
        f = Q(latest_data_status__status__name__exact='loaded') & \
            Q(latest_tested_status__status__name__in=['loaded', 'request abandoned', 'not available'])
        papers_processed_qs = papers_qs.filter(f)

        # Datasets associated with a loaded paper & growth phenotype
        p = Q(paper__in=papers_processed_qs)
        gr = Q(phenotype__observable__name__exact='growth')
        datasets_growth = datasets_qs.filter(p & gr)

        self.stdout.write('Total: %d' % datasets_growth.count())

        # Datasets associated with each type of growth
        ds = datasets_growth.values('phenotype__name').annotate(total=Count('name')).order_by('-total')

        for d in ds:
            self.stdout.write('%s\t%d' % (d, d['total']))





