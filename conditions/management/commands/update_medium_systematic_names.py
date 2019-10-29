from django.core.management.base import BaseCommand
from tqdm import tqdm

from conditions.models import Medium


class Command(BaseCommand):

    def handle(self, *args, **options):

        all_media = Medium.objects.all()

        for medium in tqdm(all_media):
            medium.save()

        self.stdout.write('Successfully updated %d media.' % all_media.count())
