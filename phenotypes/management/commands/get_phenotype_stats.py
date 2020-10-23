from django.core.management.base import BaseCommand
from django.db.models import Q, F, Count, Sum, Case, When, Min, Max
from django.db.models.functions import Concat

import numpy as np

from conditions.models import ConditionSet
from phenotypes.models import Phenotype, Observable


class Command(BaseCommand):

    def handle(self, *args, **options):

        def median_mean_std(queryset, term):
            count = queryset.count()
            values = queryset.values_list(term, flat=True)
            median = np.median(values)
            mean = np.mean(values)
            std = np.std(values)
            return median, mean, std

        phenotypes_qs = Phenotype.objects.all()

        # Total number
        phenotype_nr = phenotypes_qs.count()
        self.stdout.write('Total: %s.' % phenotype_nr)

        # Those associated with a loaded paper
        f1 = Q(dataset__paper__latest_data_status__status__name='loaded')
        phenotype_nr = phenotypes_qs.filter(f1).distinct().count()
        self.stdout.write('Loaded: %s.' % phenotype_nr)

        # Exclude growth
        g = Q(observable__name='growth')

        # Number of conditionsets per phenotype
        num_envs_per_phenotype = phenotypes_qs.filter(f1).exclude(g).\
            annotate(unique_name=Concat('dataset__conditionset', 'dataset__medium')).\
            annotate(num_envs=Count('unique_name', distinct=True))

        # Phenotypes with >1 environment
        num_phenotypes = num_envs_per_phenotype.count()
        phenotypes_w_more = num_envs_per_phenotype.order_by('-num_envs')

        for p in phenotypes_w_more[:50]:
            self.stdout.write('%s\t%d' %(p.name, p.num_envs))

        # num_phenotypes_w1_chem = num_conditionsets_per_phenotype.filter(num_conds=1).\
        #     filter(dataset__conditionset__conditions__type__tags__name='nutrient').count()

        # self.stdout.write('Num phenotypes with 1 condition: %d / %d = %.3f'
        #                   % (num_phenotypes_w1, num_phenotypes, num_phenotypes_w1/num_phenotypes))
        # self.stdout.write('Num phenotypes with 1 condition = chemical: %d' % num_phenotypes_w1_chem)





