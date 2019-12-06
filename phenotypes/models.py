from django.db import models
from django.core.urlresolvers import reverse
from django.apps import apps
from mptt.models import MPTTModel, TreeForeignKey
from django.db.models import Q


class Observable2(MPTTModel):
    """Generally the way to fetch phenotypes."""

    name = models.CharField(max_length=200)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
    #,to_field='ancestry') # See ./admin.py:Observable2Admin.to_field_allowed
    description = models.TextField(blank=True, null=True)
    definition = models.TextField(blank=True, null=True)
    modified_on = models.DateField(auto_now=True, null=True)
    ancestry = models.CharField(max_length=200, blank=True, null=True, unique=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        get_latest_by = 'modified_on'

    def __str__(self):
        return u'%s' % self.name

    def has_annotated_descendants(self):
        num_descendants = self.get_descendants(include_self=True).exclude(phenotype__dataset__isnull=True).count()
        return num_descendants > 0

    def has_annotated_relevant_descendants(self):
        f = Q(phenotype__dataset__paper__latest_data_status__status__status_name__in=['not relevant', 'request abandoned', 'not available'])
        g = Q(phenotype__dataset__isnull=True)
        num_descendants = self.get_descendants(include_self=True).exclude(f).exclude(g).count()
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

    def phenotypes(self):
        return apps.get_model('phenotypes', 'Phenotype').objects.filter(observable2=self).distinct()

    def phenotypes_list(self):
        return '; '.join([str(p) for p in self.phenotypes()[:20]])

    def phenotypes_edit_link_list(self):
        html = '<ul>'
        html = html + '<li>'.join([p.link_edit() for p in self.phenotypes()[:20]])
        html = html + '</ul>'
        return html
    phenotypes_edit_link_list.allow_tags = True

    def papers(self):
        return apps.get_model('papers', 'Paper').objects\
            .filter(dataset__phenotype__observable2=self)\
            .exclude(latest_data_status__status__status_name='not relevant')\
            .distinct()

    def papers_list(self):
        return '; '.join([str(p) for p in self.papers()])

    def papers_link_list(self):
        return '; '.join([p.link_detail() for p in self.papers()])
    papers_link_list.allow_tags = True

    def papers_edit_link_list(self):
        return '; '.join([p.link_edit() for p in self.papers()])
    papers_edit_link_list.allow_tags = True

    def conditiontypes(self):
        # Unusual specification of "not relevant" papers because, in the other way,
        # conditiontypes were being filtered out if they were associated with a "not relevant" paper at least once
        return apps.get_model('conditions', 'ConditionType').objects\
            .filter(condition__conditionset__dataset__phenotype__observable2=self,
                    condition__conditionset__dataset__paper__latest_data_status__status__lt=10)\
            .distinct()

    def conditiontypes_link_list(self):
        return ', '.join([r.link_detail() for r in self.conditiontypes()])
    conditiontypes_link_list.allow_tags = True

    def datasets(self):
        return apps.get_model('datasets', 'Dataset').objects\
            .filter(phenotype__observable2=self) \
            .exclude(paper__latest_data_status__status__status_name='not relevant')\
            .distinct()

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("phenotypes:detail", args=(self.id,)), self)
    link_detail.allow_tags = True


class Phenotype(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    observable2 = TreeForeignKey(Observable2)
    reporter = models.CharField(max_length=200, null=True, blank=True)
    modified_on = models.DateField(auto_now=True, null=True)

    def __str__(self):
        if self.reporter:
            return u'%s (%s)' % (self.observable2, self.reporter)
        else:
            return u'%s' % self.observable2

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
        return apps.get_model('papers', 'Paper').objects.filter(dataset__phenotype=self)\
            .exclude(latest_data_status__status__status_name='not relevant').distinct()

    def papers_link_list(self):
        return ', '.join([p.link_detail() for p in self.papers()])
    papers.allow_tags = True

    def papers_edit_link_list(self):
        return ', '.join([p.link_edit() for p in self.papers()])
    papers_edit_link_list.allow_tags = True

    def link_edit(self):
        html = '<a href="%s">%s</a>' % (reverse("admin:phenotypes_phenotype_change", args=(self.id,)), self)
        return html
    link_edit.allow_tags = True


class MutantType(models.Model):
    name = models.CharField(max_length=200)
    definition = models.TextField(blank=True)

    def __str__(self):
        return u'%s' % self.name


