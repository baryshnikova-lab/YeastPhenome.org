from django.core.management.base import BaseCommand
from tqdm import tqdm

from conditions.models import ConditionSet


class Command(BaseCommand):

    def handle(self, *args, **options):

        all_conditionsets = ConditionSet.objects.all()

        for conditionset in tqdm(all_conditionsets):

            # Re-generate the systematic name
            conditions_list = [(u'%s' % condition) for condition in
                               conditionset.conditions.order_by('type__group__order', 'type__chebi_name',
                                                                'type__pubchem_name', 'type__name').all()]
            conditionset.systematic_name = u'%s' % ", ".join(conditions_list)

            conditionset.display_name = conditionset.systematic_name
            if conditionset.common_name:
                conditionset.display_name = conditionset.common_name

            conditionset.save()

        self.stdout.write('Successfully updated %d conditionsets.' % all_conditionsets.count())