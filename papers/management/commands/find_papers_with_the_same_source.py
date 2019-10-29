from django.core.management.base import BaseCommand
from django.db import IntegrityError
from django.db.models import Count, Q

from papers.models import Paper
from datasets.models import Source


class Command(BaseCommand):

    def handle(self, *args, **options):

        # super(Command, self).handle(*args, **options)
        all_data_sources = Source.objects.annotate(num_papers=Count('data_source__paper', distinct=True))\
            .filter(num_papers__gt=1)

        papers_queryset = Paper.objects.all()
        f = Q(latest_data_status__status__status_name__in=['not relevant', 'request abandoned', 'not available'])
        papers_queryset = papers_queryset.exclude(f)

        for source in all_data_sources:
            papers = papers_queryset.filter(dataset__data_source=source).distinct()
            self.stdout.write('%d\t%s\t%d' % (source.num_papers, source, source.id))
            for paper in papers:
                self.stdout.write('\t%s' % paper)
