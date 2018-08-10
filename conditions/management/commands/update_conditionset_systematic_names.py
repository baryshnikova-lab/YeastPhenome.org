from django.core.management.base import BaseCommand

from conditions.models import ConditionSet


class Command(BaseCommand):

    def handle(self, *args, **options):

        all_conditionsets = ConditionSet.objects.all()

        for conditionset in all_conditionsets:
            conditionset.save()

        self.stdout.write(self.stype.SUCCESS('Successfully updated %d conditionsets.' % all_conditionsets.count()))
