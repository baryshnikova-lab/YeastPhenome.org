from django.core.management.base import BaseCommand
from django.db import IntegrityError

from datasets.models import Dataset
from tqdm import tqdm


class Command(BaseCommand):

    def handle(self, *args, **options):

        # super(Command, self).handle(*args, **options)

        all_datasets = Dataset.objects.all()

        for dataset in tqdm(all_datasets):

            try:
                dataset.save()
            except IntegrityError as e:
                self.stdout.write('Dataset %d does not have a unique name.' % dataset.id)
                pass

        self.stdout.write('Finished.')
