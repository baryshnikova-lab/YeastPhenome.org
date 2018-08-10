from django.core.management.base import BaseCommand

from conditions.models import Medium


class Command(BaseCommand):

    def handle(self, *args, **options):

        all_media = Medium.objects.all()

        for medium in all_media:
            medium.save()

        self.stdout.write(self.stype.SUCCESS('Successfully updated %d media.' % all_media.count()))
