from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db.models import Count, Q

from phenotypes.models import Observable2


class Command(BaseCommand):

    def handle(self, *args, **options):

        observable2_qs = Observable2.objects.all()

        for observable2 in observable2_qs:
            if observable2.has_annotated_relevant_descendants():
                self.stdout.write('%s\t%s\t%s' % (observable2.ancestry, observable2,
                                                      observable2.get_ancestry_names))
