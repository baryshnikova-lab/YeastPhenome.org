from django.db import models
from django.core.urlresolvers import reverse
from django.db.models import Q, Value, CharField
from django.conf import settings
from django.contrib.auth.models import User

from itertools import chain
from operator import attrgetter

from phenotypes.models import Observable2
from conditions.models import ConditionType
from datasets.models import Collection, Source

import os


class Status(models.Model):
    name = models.CharField(max_length=200, default='undefined', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_valid = models.BooleanField()

    def __str__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ['name']


class Paper(models.Model):
    first_author = models.CharField(max_length=200)
    last_author = models.CharField(max_length=200, blank=True, null=True)
    pub_date = models.IntegerField(default=0)
    pmid = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    private_notes = models.TextField(blank=True)
    modified_on = models.DateField(auto_now=True)
    user = models.ForeignKey(User, blank=True, null=True)

    data_statuses = models.ManyToManyField(Status, through='Statusdata', related_name='data_statuses')
    tested_statuses = models.ManyToManyField(Status, through='Statustested', related_name='tested_statuses')

    latest_data_status = models.ForeignKey('Statusdata', blank=True, null=True,
                                           related_name='latest_data_status_of_paper',
                                           on_delete=models.SET_NULL)
    latest_tested_status = models.ForeignKey('Statustested', blank=True, null=True,
                                             related_name='latest_tested_status_of_paper',
                                             on_delete=models.SET_NULL)

    class Meta:
        get_latest_by = 'modified_on'
        ordering =['pmid', 'first_author', 'last_author']

    def __str__(self):
        if self.last_author:
            txt = u'%s~%s, %s' % (self.first_author, self.last_author, self.pub_date)
        else:
            txt = u'%s, %s' % (self.first_author, self.pub_date)
        return txt

    def collections(self):
        return Collection.objects.filter(dataset__paper=self).distinct()

    def collections_str_list(self):
        return ', '.join([(u'%s' % i) for i in self.collections()])

    def phenotypes(self):
        return Observable2.objects.filter(phenotype__dataset__paper=self).distinct()

    def phenotypes_str_list(self):
        num = len(self.phenotypes())
        if num == 0:
            return ''
        elif num <= 20:
            return ', '.join([(u'%s' % i) for i in self.phenotypes()])
        else:
            num_remaining = num-20
            return ', '.join([(u'%s' % i) for i in self.phenotypes()[:20]]) + '... and ' + str(num_remaining) + ' more'

    def phenotypes_link_list(self):
        return ', '.join([p.link_detail() for p in self.phenotypes()])
    phenotypes_link_list.allow_tags = True

    def conditiontypes(self):
        return ConditionType.objects.filter(condition__conditionset__dataset__paper=self).distinct()

    def conditiontypes_str_list(self):
        num = len(self.conditiontypes())
        if num == 0:
            return ''
        elif num <= 20:
            return ', '.join([(u'%s' % i) for i in self.conditiontypes()])
        else:
            num_remaining = num-20
            return ', '.join([(u'%s' % i) for i in self.conditiontypes()[:20]]) + '... and ' + str(num_remaining) + ' more'

    def datasets_summary(self):
        return self.collections_str_list() + '<br>' + self.phenotypes_str_list() + '<br>' + self.conditiontypes_str_list()
    datasets_summary.allow_tags = True

    @property
    def data_published(self):
        return list(map(str, self.dataset_set.values_list('data_published', flat=True).distinct()))

    @property
    def data_available(self):
        return list(map(str, self.dataset_set.values_list('data_available', flat=True).distinct()))

    def should_have_data(self):
        # Returns True if data has been loaded from data files
        return self.latest_data_status and 'loaded' == str(self.latest_data_status.status.name)

    def raw_available_data(self):
        # Returns True if it should have data, and has access to raw data
        return self.should_have_data() and self.download_path_exists

    def download_path(self):
        # Returns a path of where datafiles should be, regardless if it has data files or not
        return os.path.join(settings.DATA_DIR, str(self.pmid))

    @property
    def download_path_exists(self):
        # Regardless if the paper should have data, returns True or False if there is a data directory for this paper
        return os.path.isdir(self.download_path())

    def static_dir_name(self):
        return "%s_%s~%s" % (self.pub_date, self.first_author.split(' ')[0],self.last_author.split(' ')[0])

    def acknowledgements_str_list(self):
        return ', '.join([(u'%s' % i) for i in Source.objects.filter(acknowledge=True)\
            .filter(Q(data_source__paper=self) | Q(tested_source__paper=self))\
            .distinct()])

    def acknowledge_data(self):
        return self.dataset_set.filter(data_source__acknowledge=True).exists()

    def acknowledge_tested(self):
        return self.dataset_set.filter(tested_source__acknowledge=True).exists()

    def latest_data_status_name(self):
        if self.latest_data_status:
            return self.latest_data_status.status.name
    latest_data_status_name.admin_order_field = 'latest_data_status__status__name'

    def latest_tested_status_name(self):
        if self.latest_tested_status:
            return self.latest_tested_status.status.name
    latest_tested_status_name.admin_order_field = 'latest_tested_status__status__name'

    def history(self):
        queryset_data = Statusdata.objects.filter(paper=self).order_by('status_date')
        queryset_tested = Statustested.objects.filter(paper=self).order_by('status_date')
        return {'data': queryset_data, 'tested strains': queryset_tested}

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("papers:detail", args=(self.id,)), self)
    link_detail.allow_tags = True

    def link_edit(self):
        html = '<a href="%s">%s</a>' % (reverse("admin:papers_paper_change", args=(self.id,)), self)
        if self.latest_data_status.status_id == 10:    # not relevant
            html = '<a href="%s" style="color: gray;">%s</a>' % (reverse("admin:papers_paper_change", args=(self.id,)), self)
        return html
    link_edit.allow_tags = True


class Statusdata(models.Model):
    paper = models.ForeignKey(Paper)
    status = models.ForeignKey(Status)
    status_date = models.DateField()

    class Meta:
        get_latest_by = 'id'

    def __str__(self):
        return u'%s' % self.status


class Statustested(models.Model):
    paper = models.ForeignKey(Paper)
    status = models.ForeignKey(Status)
    status_date = models.DateField()

    class Meta:
        get_latest_by = 'id'

    def __str__(self):
        return u'%s' % self.status


