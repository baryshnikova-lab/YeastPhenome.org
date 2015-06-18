from django.db import models
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.safestring import SafeUnicode

from phenotypes.models import Observable2
from conditions.models import ConditionType, Condition, ConditionSet
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.conf import settings

from pprint import pprint
import os
import io
import re

class Status(models.Model):
    STATUS_CHOICES = (
        ('loaded', 'loaded'),
        ('to load', 'to load'),
        ('requested', 'requested'),
        ('to request', 'to request'),
        ('waiting for tested', 'waiting for tested'),
        ('clarification needed', 'clarification needed'),
        ('not available', 'not available'),
        ('undefined', 'undefined'),
        ('abandoned','abandoned'),
    )

    status_name = models.CharField(max_length=200,
                                   choices=STATUS_CHOICES, default='undefined', blank=True, null=True)

    def __unicode__(self):
        return u'%s' % (self.status_name)


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

    class Meta:
        get_latest_by = 'modified_on'

    @property
    def collections(self):
        return list(map(str, self.dataset_set.values_list('collection', flat=True).distinct()))

    @property
    def phenotypes(self):
        result = Observable2.objects.filter(phenotype__dataset__paper=self).distinct()
        phenotype_list = ''
        for p in result:
            phenotype_list += '%s, ' % (p.link_detail())
        return phenotype_list

    @property
    def conditions(self):
        return list(map(str, ConditionType.objects.filter(condition__conditionset__dataset__paper=self).values_list(
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

    def has_data(self):
	return 'loaded'==str(self.latest_data_status()) or 'loaded'==str(self.latest_tested_status())

    @property
    def latest_data_status(self):
        return self.statusdata_set.latest

    @property
    def latest_tested_status(self):
        return self.statustested_set.latest

    def raw_file_html(self,path):
        bn=os.path.basename(path)
        dn=os.path.basename(os.path.dirname(path))
        fs=os.path.join(settings.DATASET_DIR,dn,bn)
        if os.path.isfile(fs):
            return mark_safe('<a href="/static/%s/%s">%s</a>' % (dn,bn,bn))
        else:
            return '%s (data file missing)' % (bn)

        pprint(fs)
        return bn

    def raw_files(self):
        found=[]
        stage=0

        # list of regular expression used to match file name on a
        # line.  Group(1) of the result should have a file name.
        matches=[ # don't play with them
            re.compile("(?:xlsread|textread)\('(.+?)'"),
            re.compile("datafile\s*=\s*'(.*?)'"), # only used in PMID 23552365
        ]

        for basename in os.listdir(settings.METADATA_DIR):

            # Skip files that don't end with the '.m' extention
            root,ext = os.path.splitext(basename)
            if '.m' != ext:
                if settings.DEBUG:
                    print "Skipping %s" % (basename)
            else:
                # We should now have a valid metadata file
                metadata_file=os.path.join(settings.METADATA_DIR,basename)

                if 1==stage:
                    # If we are here we found a reference to the PMID
                    # in a file but didn't find any files to load
                    # before the end of the file.  Something is
                    # probably wrong with a *.m file.
                    if settings.DEBUG:
                        print "Found PMID:%d but no files!" % (self.pmid)
                    found.append('Failed to locate files!')
                    break

                if settings.DEBUG:
                    print "opening %s" % (metadata_file)

                # Bumped into a latin1 degree sign
                md=io.open(metadata_file,encoding="ISO 8859-1")
            
                for line in md:
                    if 0==stage:
                        if re.search('\.pmid\s*=\s*%d\s*;' % self.pmid,line):
                            stage=1
                    elif 1==stage:
                        if '%' == line[0]:
                            next
                        elif re.search('^(%%|save)',line):
                            break
                        else:
                            for match in matches:
                                m=match.search(line)
                                if m:
                                    print m.group(1)
                                    found.append(self.raw_file_html(m.group(1)))
                        

                md.close()
                if 0<len(found):
                    return set(found)


        if 0==len(found):
            # Here, we found the PMID and found no files by
            # the and of the PMID section in a *.m file.
            if settings.DEBUG:
                print "Found PMID:%d but no files." % (self.pmid)
            return ['Failed to locate files.']            
        return set(found)

    def static_dir_name(self):
        return "%s_%s~%s" % (self.pub_date,self.first_author.split(' ')[0],self.last_author.split(' ')[0])

    def __unicode__(self):
        return u'%s~%s, %s' % (self.first_author, self.last_author, self.pub_date)

    def link_admin(self):
        return '<a href="%s">%s</a>' % (reverse("admin:papers_paper_change", args=(self.id,)), self)
    link_admin.allow_tags = True

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("papers:detail", args=(self.id,)), self)
    link_detail.allow_tags = True

    def sources_to_acknowledge(self):
        result = Source.objects.filter(Q(acknowledge = True) & (Q(data_source__paper = self) | Q(tested_source__paper = self))).values_list('person', flat=True).distinct()
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
    date = models.DateField()
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

