from django.core.management.base import BaseCommand

from conditions.models import Medium


class Command(BaseCommand):

    def handle(self, *args, **options):

        all_media = Medium.objects.all()

        for medium in all_media:
            output_str = '%d\t%s\t%s\t%s'
            output_vals = (medium.id, medium, medium.conditions_str_list(), medium.paper_str_list())
            self.stdout.write(output_str % output_vals)

        # self.stdout.write(self.stype.SUCCESS('Finished.'))
