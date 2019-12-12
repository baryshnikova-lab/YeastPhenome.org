from django.core.management.base import BaseCommand
from django.db import IntegrityError

from datasets.models import Dataset


class Command(BaseCommand):

    def handle(self, *args, **options):

        # super(Command, self).handle(*args, **options)cd

        all_datasets = Dataset.objects.filter(data_source__isnull=True).\
            filter(paper__latest_data_status__status__name__in=['loaded']).distinct()

        for dataset in all_datasets:
            self.stdout.write('%s' % dataset.name)

        self.stdout.write('Finished.')
