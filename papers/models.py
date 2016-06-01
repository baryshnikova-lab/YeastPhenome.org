from django.db import models
from django.core.urlresolvers import reverse
from django.db.models import Q, Value, CharField
from django.conf import settings
from django.contrib.auth.models import User

from itertools import chain
from operator import attrgetter

from phenotypes.models import Observable2
from conditions.models import ConditionType

import os


class Status(models.Model):
    status_name = models.CharField(max_length=200,
                                   default='undefined', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.status_name

    class Meta:
        ordering = ['status_name']


class Paper(models.Model):
    first_author = models.CharField(max_length=200)
    last_author = models.CharField(max_length=200)
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

    def __unicode__(self):
        return u'%s~%s, %s' % (self.first_author, self.last_author, self.pub_date)

    def collections(self):
        return Collection.objects.filter(dataset__paper=self).distinct()

    def collections_str_list(self):
        return ', '.join([(u'%s' % i) for i in self.collections()])

    def phenotypes(self):
        return Observable2.objects.filter(phenotype__dataset__paper=self).distinct()

    def phenotypes_str_list(self):
        return ', '.join([(u'%s' % i) for i in self.phenotypes()])

    def phenotypes_link_list(self):
        return ', '.join([p.link_detail() for p in self.phenotypes()])
    phenotypes_link_list.allow_tags = True

    def conditiontypes(self):
        return ConditionType.objects.filter(condition__conditionset__dataset__paper=self).distinct()

    def conditiontypes_str_list(self):
        return ', '.join([(u'%s' % i) for i in self.conditiontypes()])

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
        return self.latest_data_status and 'loaded' == str(self.latest_data_status.status.status_name)

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
        return self.dataset_set.filter(data_source__acknowledge = True).exists()

    def acknowledge_tested(self):
        return self.dataset_set.filter(tested_source__acknowledge = True).exists()

    def latest_data_status_name(self):
        if self.latest_data_status:
            return self.latest_data_status.status.status_name
    latest_data_status_name.admin_order_field = 'latest_data_status__status__status_name'

    def latest_tested_status_name(self):
        if self.latest_tested_status:
            return self.latest_tested_status.status.status_name
    latest_tested_status_name.admin_order_field = 'latest_tested_status__status__status_name'

    def history(self):
        queryset1 = Statusdata.objects.filter(paper=self).all().annotate(type=Value('data', CharField()))
        queryset2 = Statustested.objects.filter(paper=self).all().annotate(type=Value('tested strains', CharField()))
        result_list = sorted(chain(queryset1, queryset2), key=attrgetter('status_date'))
        return result_list

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("papers:detail", args=(self.id,)), self)
    link_detail.allow_tags = True

    def link_edit(self):
        return '<a href="%s">%s</a>' % (reverse("admin:papers_paper_change", args=(self.id,)), self)
    link_edit.allow_tags = True


class Statusdata(models.Model):
    paper = models.ForeignKey(Paper)
    status = models.ForeignKey(Status)
    status_date = models.DateField()

    class Meta:
        get_latest_by = 'id'

    def __unicode__(self):
        return u'%s' % self.status


class Statustested(models.Model):
    paper = models.ForeignKey(Paper)
    status = models.ForeignKey(Status)
    status_date = models.DateField()

    class Meta:
        get_latest_by = 'id'

    def __unicode__(self):
        return u'%s' % self.status


class Collection(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    shortname = models.CharField(max_length=200, null=True, blank=True)
    matingtype = models.CharField(max_length=200, null=True, blank=True)
    ploidy = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.shortname


class Sourcetype(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    shortname = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        return u'%s' % self.name


class Source(models.Model):
    sourcetype = models.ForeignKey(Sourcetype, null=True, blank=True, related_name='sourcetype')
    link = models.CharField(max_length=200, null=True, blank=True)
    person = models.CharField(max_length=200, null=True, blank=True)
    date = models.DateField(null=True)
    acknowledge = models.NullBooleanField()
    release = models.NullBooleanField()

    def __unicode__(self):
        if self.person == '':
            return u'%s' % self.sourcetype
        else:
            return u'%s' % self.person

    def papers(self):
        return Paper.objects.filter(dataset__tested_source=self).distinct()

    def papers_str_list(self):
        return ', '.join([(u'%s' % p) for p in self.papers()])


class Dataset(models.Model):
    paper = models.ForeignKey(Paper)
    conditionset = models.ForeignKey('conditions.ConditionSet', null=True, blank=True)
    phenotype = models.ForeignKey('phenotypes.Phenotype', null=True, blank=True)
    collection = models.ForeignKey(Collection, null=True, blank=True)

    notes = models.TextField(null=True, blank=True)

    tested_num = models.IntegerField(default=0, null=True)
    tested_list_published = models.NullBooleanField()
    tested_source = models.ForeignKey(Source, null=True, blank=True, related_name='tested_source')

    DATA_CHOICES = (
        ('quantitative', 'quantitative'),
        ('quantitative only for hits', 'quantitative only for hits'),
        ('discrete', 'discrete'),
        ('none', 'none'),
        ('unknown', 'unknown'),
    )

    data_measured = models.CharField(max_length=200,
                                     choices=DATA_CHOICES,
                                     null=True, blank=True)
    data_published = models.CharField(max_length=200,
                                      choices=DATA_CHOICES,
                                      null=True, blank=True)
    data_available = models.CharField(max_length=200,
                                      choices=DATA_CHOICES,
                                      null=True, blank=True)

    data_source = models.ForeignKey(Source, null=True, blank=True, related_name='data_source')

    def __unicode__(self):
        return u'%s | %s | %s | %s | %s | %s' % (self.collection, self.phenotype, self.conditionset,
                                                 self.data_measured, self.data_published, self.data_available)

    class Meta:
        ordering = ['id']

    def tested_genes_published(self):
        return self.tested_list_published
    tested_genes_published.boolean = True

    def tested_space(self):
        if self.tested_source and self.data_set.exists():
            tested_space = self.data_set.count()
        elif self.tested_num > 0:
            tested_space = '<abbr title="Estimated number of tested mutants. The exact list of tested mutants is not available.">~%s</abbr>' % self.tested_num
        else:
            tested_space = 'N/A'
        return tested_space
    tested_space.allow_tags = True

    def phenotypes(self):
        return self.observable2.name

    def has_data_in_db(self):
        return self.data_set.exists()
    has_data_in_db.boolean = True


class Data(models.Model):
    dataset = models.ForeignKey(Dataset)
    value = models.DecimalField(max_digits=10, decimal_places=3)
    orf = models.CharField(max_length=50)

    def __unicode__(self):
        return u'%s - %s' % (self.orf, self.value)

