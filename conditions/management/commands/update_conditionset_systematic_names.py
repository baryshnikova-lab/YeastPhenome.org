from django.core.management.base import BaseCommand
from tqdm import tqdm

from conditions.models import ConditionSet


class Command(BaseCommand):

    def handle(self, *args, **options):

        all_conditionsets = ConditionSet.objects.all()

        for conditionset in tqdm(all_conditionsets):
            conditionset.save()

        self.stdout.write('Successfully updated %d conditionsets.' % all_conditionsets.count())