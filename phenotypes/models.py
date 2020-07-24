from django.db import models
from django.core.urlresolvers import reverse
from django.apps import apps
from mptt.models import MPTTModel, TreeForeignKey
from django.db.models import Q


class Tag(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField(max_length=1000, null=True, blank=True)

    def __str__(self):
        return self.name

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("phenotypes:tag", args=(self.id,)), self)
    link_detail.allow_tags = True

    def link_edit(self):
        html = '<a href="%s">%s</a>' % (reverse("admin:phenotypes_tag_change", args=(self.id,)), self)
        return html
    link_edit.allow_tags = True

    def observables(self):
        return apps.get_model('phenotypes', 'Observable').objects.filter(tags=self).order_by('name').all()

    def observables_str_list(self):
        return '; '.join([str(o) for o in self.observables()])

    def observables_edit_link_list(self):
        html = '<ul>'
        html = html + '<li>'.join([p.link_edit() for p in self.observables()])
        html = html + '</ul>'
        return html
    observables_edit_link_list.allow_tags = True


class Observable(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    modified_on = models.DateField(auto_now=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        get_latest_by = 'modified_on'

    def __str__(self):
        return u'%s' % self.name

    def link_edit(self):
        html = '<a href="%s">%s</a>' % (reverse("admin:phenotypes_observable_change", args=(self.id,)), self)
        return html
    link_edit.allow_tags = True

    def get_tags(self):
        return self.tags.order_by('name').all()

    def tags_str_list(self):
        return ", ".join([(u'%s' % t) for t in self.get_tags()])

    def tags_edit_link_list(self):
        html = '<ul>'
        html = html + '<li>'.join([p.link_edit() for p in self.get_tags()])
        html = html + '</ul>'
        return html
    tags_edit_link_list.allow_tags = True

    def phenotypes(self):
        return apps.get_model('phenotypes', 'Phenotype').objects.filter(observable=self).distinct()

    def phenotypes_list(self):
        return '; '.join([str(p) for p in self.phenotypes()[:20]])

    def phenotypes_edit_link_list(self):
        html = '<ul>'
        html = html + '<li>'.join([p.link_edit() for p in self.phenotypes()[:20]])
        html = html + '</ul>'
        return html
    phenotypes_edit_link_list.allow_tags = True

    def datasets(self):
        return apps.get_model('datasets', 'Dataset').objects.filter(phenotype__observable=self).all()

    def datasets_edit_link_list(self):
        html = '<ul>'
        html = html + '<li>'.join([d.link_edit() for d in self.datasets()[:50]])
        html = html + '</ul>'
        return html
    datasets_edit_link_list.allow_tags = True

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("phenotypes:detail", args=(self.id,)), self)
    link_detail.allow_tags = True

    def conditiontypes(self):
        # Unusual specification of "not relevant" papers because, in the other way,
        # conditiontypes were being filtered out if they were associated with a "not relevant" paper at least once
        return apps.get_model('conditions', 'ConditionType').objects\
            .filter(condition__conditionset__dataset__phenotype__observable=self,
                    condition__conditionset__dataset__paper__latest_data_status__status__lt=10)\
            .distinct()

    def papers(self):
        return apps.get_model('papers', 'Paper').objects\
            .filter(dataset__phenotype__observable=self)\
            .exclude(latest_data_status__status__name='not relevant')\
            .distinct()

    def papers_str_list(self):
        return '; '.join([(u'%s' % p) for p in self.papers()])


class Observable2(MPTTModel):
    """Generally the way to fetch phenotypes."""

    name = models.CharField(max_length=200)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children')
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
        f = Q(phenotype__dataset__paper__latest_data_status__status__is_valid=True)
        g = Q(phenotype__dataset__isnull=False)
        num_descendants = self.get_descendants(include_self=True).filter(f).filter(g).count()
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

    def get_ancestry_names(self):
        ancestors = self.get_ancestors(ascending=False, include_self=False)
        a = []
        for r in ancestors:
            a.append(r.name)
        return '; '.join(a)

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
            .exclude(latest_data_status__status__name='not relevant')\
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
        return apps.get_model('papers', 'Dataset').objects\
            .filter(phenotype__observable2=self) \
            .exclude(paper__latest_data_status__status__name='not relevant')\
            .distinct()

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("phenotypes:detail", args=(self.id,)), self)
    link_detail.allow_tags = True


class Measurement(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def __str__(self):
        return u'%s' % self.name

    def phenotypes(self):
        return apps.get_model('phenotypes', 'Phenotype').objects.filter(measurement=self)

    def phenotypes_edit_link_list(self):
        html = '<ul>'
        html = html + '<li>'.join([ph.link_edit() for ph in self.phenotypes()[:20]])
        html = html + '</ul>'
        return html
    phenotypes_edit_link_list.allow_tags = True


class Phenotype(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    observable2 = TreeForeignKey(Observable2, blank=True, null=True)
    observable = models.ForeignKey(Observable, blank=False, null=False)
    reporter = models.CharField(max_length=200, blank=True, null=True)
    measurement = models.ForeignKey(Measurement, blank=True, null=True)
    modified_on = models.DateField(auto_now=True, null=True)

    def __str__(self):
        if self.reporter:
            return u'%s (%s)' % (self.observable, self.reporter)
        else:
            return u'%s' % self.observable

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("phenotypes:detail", args=(self.observable.id,)), self)
    link_detail.allow_tags = True

    def link_edit(self):
        html = '<a href="%s">%s</a>' % (reverse("admin:phenotypes_phenotype_change", args=(self.id,)), self)
        return html
    link_edit.allow_tags = True

    def ancestry(self):
        ancestors = self.observable2.get_ancestors(ascending=False, include_self=True)
        r = ''
        for a in ancestors:
            r += '%d.' % a.id
        return '%s %s' % ('--' * len(ancestors), r)

    def observable2_name(self):
        return '<span style="white-space: nowrap;">%s %s</span>' % (self.ancestry(), self.observable2.name)
    observable2_name.allow_tags = True

    def observable_name(self):
        return self.observable.name

    def papers(self):
        return apps.get_model('papers', 'Paper').objects.filter(dataset__phenotype=self)\
            .exclude(latest_data_status__status__name='not relevant').distinct()

    def papers_link_list(self):
        return ', '.join([p.link_detail() for p in self.papers()])
    papers.allow_tags = True

    def papers_edit_link_list(self):
        return ', '.join([p.link_edit() for p in self.papers()])
    papers_edit_link_list.allow_tags = True

    def datasets(self):
        return apps.get_model('datasets', 'Dataset').objects.filter(phenotype=self).all()

    def datasets_edit_link_list(self):
        html = '<ul>'
        html = html + '<li>'.join([d.link_edit() for d in self.datasets()[:50]])
        html = html + '</ul>'
        return html
    datasets_edit_link_list.allow_tags = True


class MutantType(models.Model):
    name = models.CharField(max_length=200)
    definition = models.TextField(blank=True)

    def __str__(self):
        return u'%s' % self.name
