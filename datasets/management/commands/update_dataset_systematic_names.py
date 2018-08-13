from django.core.management.base import BaseCommand

from datasets.models import Dataset
from tqdm import tqdm


class Command(BaseCommand):

    def handle(self, *args, **options):

        all_datasets = Dataset.objects.all()

        for dataset in tqdm(all_datasets):
            dataset.save()

        self.stdout.write(self.stype.SUCCESS('Successfully updated all datasets.'))
