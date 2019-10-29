from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db.models import Count, Q

from papers.models import Paper


class Command(BaseCommand):

    def handle(self, *args, **options):

        # super(Command, self).handle(*args, **options)

        papers_queryset = Paper.objects.all()
        f = Q(latest_data_status__status__status_name__in=['not relevant', 'request abandoned', 'not available'])
        g = Q(dataset__medium__isnull=True)
        papers_queryset = papers_queryset.exclude(f).filter(g).distinct()

        for paper in papers_queryset:
            self.stdout.write('%s' % paper)
