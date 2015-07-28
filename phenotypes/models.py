from django.db import models
from django.core.urlresolvers import reverse
from django.apps import apps
from mptt.models import MPTTModel, TreeForeignKey

class Observable2(MPTTModel):
    """Generally the way to fetch phenotypes."""

    name = models.CharField(max_length=200)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    description = models.TextField(blank=True, null=True)
    definition = models.TextField(blank=True, null=True)
    modified_on = models.DateField(auto_now=True, null=True)
    ancestry = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        return u'%s' % self.name

    def has_annotated_descendants(self):
        num_descendants = self.get_descendants(include_self=True).exclude(phenotype__dataset__isnull=True).count()
        return num_descendants > 0

    def get_ancestry(self):
        ancestors = self.get_ancestors(ascending=False, include_self=True)
        a = ''
        for r in ancestors:
            a += '%03d.' % r.id
        return a

    def get_ancestry_short(self):
        ancestors = self.get_ancestors(ascending=False, include_self=True)
        a = ''
        for r in ancestors:
            a += '%d.' % r.id
        return a

    def paper_list(self):
        # Returns a list of papers associated with this Observable
        return apps.get_model('papers','Paper').objects.filter(dataset__phenotype__observable2=self).distinct()

    def papers(self):
        # Return HTML list of papers
        result = self.paper_list()
        l = ''
        for p in result:
            l += '%s, ' % (p.link_detail())
        return l

    def condition_types(self):
        result = apps.get_model('conditions','ConditionType').objects.filter(condition__conditionset__dataset__phenotype__observable2=self).distinct()
        l = ''
        for r in result:
            l += '%s, ' % (r.link_detail())
        return l

    def datasets(self):
        return apps.get_model('papers','Dataset').objects.filter(phenotype__observable2=self).distinct()

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("phenotypes:detail", args=(self.id,)), self)
    link_detail.allow_tags = True

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        get_latest_by = 'modified_on'


class Phenotype(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    observable2 = TreeForeignKey(Observable2)
    reporter = models.CharField(max_length=200, null=True, blank=True)
    modified_on = models.DateField(auto_now=True, null=True)

    def __unicode__(self):
        if self.reporter == '':
            return u'%s' % self.observable2
        else:
            return u'%s (%s)' % (self.observable2, self.reporter)

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("phenotypes:detail", args=(self.observable2.id,)), self)
    link_detail.allow_tags = True

    def ancestry(self):
        ancestors = self.observable2.get_ancestors(ascending=False, include_self=True)
        r = ''
        for a in ancestors:
            r += '%d.' % a.id
        return '%s %s' % ('--' * len(ancestors), r)

    def observable2_name(self):
        return '<span style="white-space: nowrap;">%s %s</span>' % (self.ancestry(), self.observable2.name)
    observable2_name.allow_tags = True

    def papers(self):
        result = apps.get_model('papers','Paper').objects.filter(dataset__phenotype=self).distinct()
        l = ''
        for p in result:
            l += '%s, ' % (p.link_detail())
        return l
    papers.allow_tags = True


class MutantType(models.Model):
    name = models.CharField(max_length=200)
    definition = models.TextField(blank=True)

    def __unicode__(self):
        return u'%s' % self.name


