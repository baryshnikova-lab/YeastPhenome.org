from django.core.management.base import BaseCommand
from tqdm import tqdm

from conditions.models import Medium


class Command(BaseCommand):

    def handle(self, *args, **options):

        all_media = Medium.objects.all()

        for medium in tqdm(all_media):

            # Re-generate the systematic name
            conditions_list = [(u'%s' % condition) for condition in
                               medium.conditions.order_by('type__tags__order', 'type__chebi_name',
                                                          'type__pubchem_name', 'type__name').all()]
            medium.systematic_name = u'%s' % ", ".join(conditions_list)

            medium.display_name = medium.systematic_name
            if medium.common_name:
                medium.display_name = medium.common_name

            medium.save()

        self.stdout.write('Successfully updated %d media.' % all_media.count())
