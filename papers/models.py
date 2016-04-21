from django.db import models
from django.core.urlresolvers import reverse
from django.db.models import Q

from django.conf import settings
from django.contrib.auth.models import User
from phenotypes.models import Observable2
from conditions.models import ConditionType, ConditionSet

import os
import warnings


class Status(models.Model):
    status_name = models.CharField(max_length=200,
                                   default='undefined', blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.status_name


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

    @property
    def collections(self):
        return list(map(str, self.dataset_set.values_list('collection', flat=True).distinct()))

    def phenotype_list(self):
        # Returns a list of Observable2 objects that this paper is in
        return Observable2.objects.filter(phenotype__dataset__paper=self).distinct()

    @property
    def phenotypes(self):
        # Returns a string containing the list of phenotypes for this paper
        return ', '.join([unicode(i) for i in self.phenotype_list()])

    @property
    def phenotypes_links(self):
        # Returns a string containing the list of phenotypes (with links) for this paper
        result = self.phenotype_list()
        phenotype_list = ''
        for p in result:
            phenotype_list += '%s, ' % (p.link_detail())
        return phenotype_list

    def condition_list(self):
        # Returns a QuerySet of conditions associated with this paper
        return ConditionType.objects.filter(condition__conditionset__dataset__paper=self)

    @property
    def conditions(self):
        return list(map(str, self.condition_list().values_list(
            'short_name', flat=True).distinct()))

    @property
    def condition_sets(self):
        return list(set([condition_set.by_conditiontype() for condition_set in ConditionSet.objects.filter(dataset__paper=self).distinct()]))

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
        return "%s_%s~%s" % (self.pub_date,self.first_author.split(' ')[0],self.last_author.split(' ')[0])

    def __unicode__(self):
        return u'%s~%s, %s' % (self.first_author, self.last_author, self.pub_date)

    def link_admin(self):
        return '<a href="%s">%s</a>' % (reverse("admin:papers_paper_change", args=(self.id,)), self)
    link_admin.allow_tags = True

    def link_detail(self):
        warnings.warn("link_detail", DeprecationWarning)
        return '<a href="%s">%s</a>' % (reverse("papers:detail", args=(self.id,)), self)
    link_detail.allow_tags = True

    def sources_to_acknowledge(self):
        result = Source.objects.filter(Q(acknowledge=True) & (Q(data_source__paper=self) | Q(tested_source__paper=self))).values_list('person', flat=True).distinct()
        result_list = ''
        for r in result:
            result_list += u'%s ' % (r)
        return result_list

    def got_data(self):
        result = self.dataset_set.filter(data_source__acknowledge = True).distinct()
        return len(result) > 0

    def got_tested(self):
        result = self.dataset_set.filter(tested_source__acknowledge = True).distinct()
        return len(result) > 0

    def dataset_list(self):
        # Like dataset_set.all() but returns a sorted list
        dss = self.dataset_set.all()
        out = []
        for ds in dss:
            out.append(ds)
        out.sort(lambda a, b: cmp(a.sort_string(), b.sort_string()))
        return out


class Statusdata(models.Model):
    paper = models.ForeignKey(Paper)
    status = models.ForeignKey(Status)
    status_date = models.DateField()

    class Meta:
        get_latest_by = 'id'

    def __unicode__(self):
        return u'%s' % (self.status)


class Statustested(models.Model):
    paper = models.ForeignKey(Paper)
    status = models.ForeignKey(Status)
    status_date = models.DateField()

    class Meta:
        get_latest_by = 'id'

    def __unicode__(self):
        return u'%s' % (self.status)


class Collection(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    shortname = models.CharField(max_length=200, null=True, blank=True)
    matingtype = models.CharField(max_length=200, null=True, blank=True)
    ploidy = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return u'%s' % (self.shortname)


class Sourcetype(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    shortname = models.CharField(max_length=200, null=True, blank=True)

    def __unicode__(self):
        return u'%s' % (self.name)


class Source(models.Model):
    sourcetype = models.ForeignKey(Sourcetype, null=True, blank=True, related_name='sourcetype')
    link = models.CharField(max_length=200, null=True, blank=True)
    person = models.CharField(max_length=200, null=True, blank=True)
    date = models.DateField(null=True)
    acknowledge = models.NullBooleanField()
    release = models.NullBooleanField()

    def papers(self):
        result = Paper.objects.filter(dataset__tested_source=self).distinct()
        list = ''
        for p in result:
            list += '%s, ' % (p)
        return list

    def __unicode__(self):
        if self.person == '':
            return u'%s' % self.sourcetype
        else:
            return u'%s' % self.person

    def change_link(self):
        return '<a href="%s" target="_blank">Edit</a>' % (reverse("admin:papers_source_change", args=(self.id,)))
    change_link.allow_tags = True


class Dataset(models.Model):
    paper = models.ForeignKey(Paper)
    conditionset = models.ForeignKey('conditions.ConditionSet', null=True, blank=True)
    phenotype = models.ForeignKey('phenotypes.Phenotype', null=True, blank=True)
    collection = models.ForeignKey(Collection, null=True, blank=True)

    notes = models.TextField(null=True, blank=True)

    tested_num = models.IntegerField(default=0, null=True)
    tested_list_published = models.NullBooleanField()
    tested_source = models.ForeignKey(Source, null=True, blank=True, related_name='tested_source')
    tested_can_release = models.NullBooleanField()

    DATA_CHOICES = (
        ('quantitative', 'quantitative'),
        ('quantitative only for hits', 'quantitative only for hits'),
        ('discrete', 'discrete'),
        ('no data released', 'no data released'),
        ('unknown', 'unknown'),
    )

    data_measured = models.CharField(max_length=200,
                                     choices=DATA_CHOICES,
                                     default='UNK', null=True, blank=True)
    data_published = models.CharField(max_length=200,
                                      choices=DATA_CHOICES,
                                      default='UNK', null=True, blank=True)
    data_available = models.CharField(max_length=200,
                                      choices=DATA_CHOICES,
                                      default='UNK', null=True, blank=True)

    data_source = models.ForeignKey(Source, null=True, blank=True, related_name='data_source')
    data_can_release = models.NullBooleanField()

    def __unicode__(self):
        return u'(%s, %s, %s)' % (self.collection, self.phenotype, self.conditionset)

    def sort_string(self):
        # Just to make things easier to sort
        out = u"%s %s %s %d %s" % (self.phenotype,
                                   self.conditionset,
                                   self.collection,
                                   self.tested_num,
                                   self.data_available)
        return out.lower()

    def tested_genes_published(self):
        return self.tested_list_published
    tested_genes_published.boolean = True
    tested_genes_published.allow_tags = True

    def phenotypes(self):
        return self.observable2.name

    def changetestedsource_link(self):
        return self.tested_source.change_link()
    changetestedsource_link.allow_tags = True

    def changedatasource_link(self):
        return self.data_source.change_link()
    changedatasource_link.allow_tags = True

    def has_data(self):
        return self.data_set.exists()
    has_data.boolean = True


class Data(models.Model):
    dataset = models.ForeignKey(Dataset, null=True, blank=True)
    value = models.DecimalField(max_digits=10, decimal_places=3)
    orf = models.CharField(max_length=50, null=True, blank=True)

    def __unicode__(self):
        return u'%s - %f' % (self.orf, self.value)

