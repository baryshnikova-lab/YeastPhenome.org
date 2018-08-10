from __future__ import unicode_literals

from django.db import models
from django.apps import apps
from django.contrib.humanize.templatetags.humanize import intcomma


class Collection(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    shortname = models.CharField(max_length=200, null=True, blank=True)
    matingtype = models.CharField(max_length=200, null=True, blank=True)
    ploidy = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return u'%s' % self.shortname


class Sourcetype(models.Model):
    name = models.CharField(max_length=200, null=True, blank=True)
    shortname = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return u'%s' % self.name


class Source(models.Model):
    sourcetype = models.ForeignKey(Sourcetype, null=True, blank=True, related_name='sourcetype')
    link = models.TextField(max_length=200, null=True, blank=True)
    person = models.CharField(max_length=200, null=True, blank=True)
    date = models.DateField(null=True)
    acknowledge = models.NullBooleanField()
    release = models.NullBooleanField()

    def __str__(self):
        if self.person:
            return u'%s' % self.person
        else:
            return u'%s' % self.sourcetype

    def html(self):
        if self.person:
            return u'%s' % self.person
        else:
            if self.link:
                return u'<a class="external" href="%s">%s</a>' % (self.link, self.sourcetype)
            else:
                return u'%s' % self.sourcetype
    html.allow_tags = True

    def link_or_person(self):
        if self.person:
            return u'%s' % self.person
        else:
            if self.link:
                return u'%s...' % self.link[:min(60, len(self.link))]
            else:
                return u'unknown'

    def papers(self):
        return apps.get_model('papers', 'Paper').objects.filter(dataset__tested_source=self).distinct()

    def papers_str_list(self):
        return ', '.join([(u'%s' % p) for p in self.papers()])


class Dataset(models.Model):
    name = models.CharField(max_length=500, null=True, blank=True)
    paper = models.ForeignKey('papers.Paper')

    conditionset = models.ForeignKey('conditions.ConditionSet', null=True, blank=True)
    medium = models.ForeignKey('conditions.Medium', null=True, blank=True)

    control_conditionset = models.ForeignKey('conditions.ConditionSet', related_name='control_conditionset',
                                             null=True, blank=True)
    control_medium = models.ForeignKey('conditions.Medium', related_name='control_medium',
                                       null=True, blank=True)

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

    def __str__(self):
        return u'%s' % self.name

    def admin_name(self):
        data_info = [self.data_measured, self.data_published, self.data_available]
        data_info_acronym = []
        for dt in data_info:
            data_info_acronym.append("".join(word[0] for word in dt.split()))
        data_all = u'%s | %s' % (self.name, ", ".join(data_info_acronym))
        return data_all

    class Meta:
        ordering = ['id']

    def tested_genes_published(self):
        return self.tested_list_published
    tested_genes_published.boolean = True

    def tested_genes_available(self):
        return self.tested_source is not None
    tested_genes_available.boolean = True

    def tested_space(self):
        if self.tested_source and self.data_set.exists():
            tested_space = intcomma(self.data_set.count())
        elif self.tested_num and self.tested_num > 0:
            tested_space = '<abbr title="The list of tested mutants is not available. This is an approximate number of tested mutants as reported by the authors.">~%s</abbr>' % intcomma(self.tested_num)
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

    def __str__(self):
        return u'%s - %s' % (self.orf, self.value)