from django.db import models
from django.core.urlresolvers import reverse
from django.apps import apps
from phenotypes.models import Phenotype


class ConditionType(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    short_name = models.CharField(max_length=200, blank=True, null=True)

    pubchem_id = models.PositiveIntegerField(blank=True, null=True, unique=True)
    pubchem_name = models.CharField(max_length=200, blank=True, null=True)

    chebi_id = models.PositiveIntegerField(blank=True, null=True, unique=True)
    chebi_name = models.CharField(max_length=200, blank=True, null=True)

    CONDITION_GROUP_CHOICES = (
        ('chemical', 'chemical'),
        ('physical', 'physical'),
        ('nutrient', 'nutrient'),
        ('other', 'other'),
    )

    group = models.CharField(max_length=200,
                             choices=CONDITION_GROUP_CHOICES,
                             blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        if self.chebi_name:
            type_name = self.chebi_name
        elif self.pubchem_name:
            type_name = self.pubchem_name
        elif self.short_name:
            type_name = self.short_name
        else:
            type_name = self.name
        return u'%s' % type_name

    def conditions(self):
        return ', '.join([p.dose for p in Condition.objects.filter(type=self).order_by('dose')])

    def phenotypes(self):
        result = Phenotype.objects.filter(dataset__conditionset__conditions__type=self).distinct()
        list = ''
        for p in result:
            list += '%s, ' % (p.link_detail())
        return list

    def paper_list(self):
        # Returns a QuerySet of Papers with this ConditionType.
        return apps.get_model('papers','Paper').objects.filter(dataset__conditionset__conditions__type=self).distinct()

    def papers(self):
        # Returns a string containing HTML for all the papers.
        result = self.paper_list()
        l = ''
        for p in result:
            l += '%s, ' % (p.link_detail())
        return l

    def datasets(self):
        return apps.get_model('papers', 'Dataset').objects.filter(conditionset__conditions__type=self).distinct()

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("conditions:detail", args=(self.id,)), self)
    link_detail.allow_tags = True


class Condition(models.Model):
    type = models.ForeignKey(ConditionType)
    dose = models.CharField(max_length=200, null=False, blank=False)
    modified_on = models.DateField(auto_now=True, null=True)

    class Meta:
        get_latest_by = 'modified_on'

    def __unicode__(self):
        return u'%s [%s]' % (self.type, self.dose)

    def condition_sets(self):
        result = ConditionSet.objects.filter(conditions=self).all()
        l = ''
        for p in result:
            l += '%s, ' % (p.conditionset_link())
        return l
    condition_sets.allow_tags = True


class ConditionSet(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    conditions = models.ManyToManyField(Condition)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        conditions_list = ", ".join([unicode(condition) for condition in self.conditions.all()])
        if self.name == '':
            return conditions_list
        else:
            return u'%s (%s)' % (self.name, conditions_list)

    def papers(self):
        result = apps.get_model('papers','Paper').objects.filter(dataset__conditionset=self).all()
        papers_list = ''
        for p in result:
            papers_list += '%s, ' % (p.link_detail())
        return papers_list
    papers.allow_tags = True

    # def datasets(self):
    #     return apps.get_model('papers','Dataset').objects.filter(conditionset=self).distinct()

    def conditionset_link(self):
        return '{<a href="%s">%s</a>}' % (reverse("admin:conditions_conditionset_change", args=(self.id,)), self)
    conditionset_link.allow_tags = True
