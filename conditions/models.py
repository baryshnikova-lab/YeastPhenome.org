from django.db import models
from django.core.urlresolvers import reverse
from django.apps import apps

from phenotypes.models import Phenotype

from libchebipy import ChebiEntity


class ConditionType(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    other_names = models.TextField(blank=True, null=True)

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

    class Meta:
        ordering = ['group', 'chebi_name', 'pubchem_name', 'name', 'other_names']

    def __unicode__(self):
        if self.chebi_name:
            type_name = self.chebi_name
        elif self.pubchem_name:
            type_name = self.pubchem_name
        elif self.name:
            type_name = self.name
        else:
            type_name = self.other_names
        return u'%s' % type_name

    def definition(self):
        if self.chebi_id:
            entity = ChebiEntity('CHEBI:' + str(self.chebi_id))
            return entity.get_definition()
        else:
            return ''

    def has_roles(self):
        if self.chebi_id:
            entity = ChebiEntity('CHEBI:' + str(self.chebi_id))
            outdict = dict()
            for relation in entity.get_outgoings():
                if relation.get_type() == 'has_role':
                    tid = relation.get_target_chebi_id()
                    t = ChebiEntity(tid)
                    outdict[t.get_name()] = tid
            return outdict
        else:
            return ''

    def conditions(self):
        return Condition.objects.filter(type=self).order_by('dose')

    def conditions_str_list(self):
        return ', '.join([p.dose for p in self.conditions()])

    def phenotypes(self):
        return Phenotype.objects.filter(dataset__conditionset__conditions__type=self).distinct()

    def phenotypes_link_list(self):
        return ', '.join([p.link_detail() for p in self.phenotypes()])
    phenotypes_link_list.allow_tags = True

    def papers(self):
        return apps.get_model('papers', 'Paper').objects.filter(dataset__conditionset__conditions__type=self)\
            .exclude(latest_data_status__status__status_name='not relevant').distinct()

    def papers_link_list(self):
        return ', '.join([(u'%s' % p.link_detail()) for p in self.papers()])
    papers_link_list.allow_tags = True

    def datasets(self):
        return apps.get_model('datasets', 'Dataset').objects.filter(conditionset__conditions__type=self)\
            .exclude(paper__latest_data_status__status__status_name='not relevant').distinct()

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

    def conditionsets(self):
        return ConditionSet.objects.filter(conditions=self).all()

    def conditionsets_str_list(self):
        return ", ".join([p.link_edit() for p in self.conditionsets()])
    conditionsets_str_list.allow_tags = True

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("conditions:detail", args=(self.type.id,)), self)
    link_detail.allow_tags = True


class ConditionSet(models.Model):
    name = models.CharField(max_length=200, blank=True, null=True)
    conditions = models.ManyToManyField(Condition)
    description = models.TextField(blank=True, null=True)

    def __unicode__(self):
        conditions_list = ", ".join([(u'%s' % condition) for condition in self.conditions.order_by('type__group','type__chebi_name','type__pubchem_name','type__name')])
        if not self.name or self.name == '':
            return u'%s' % conditions_list
        else:
            return u'%s (%s)' % (self.name, conditions_list)

    def papers(self):
        return apps.get_model('papers', 'Paper').objects.filter(dataset__conditionset=self).distinct()

    def papers_link_list(self):
        return ', '.join([p.link_detail() for p in self.papers()])
    papers_link_list.allow_tags = True

    def papers_edit_link_list(self):
        return ', '.join([p.link_edit() for p in self.papers()])
    papers_edit_link_list.allow_tags = True

    # def datasets(self):
    #     return apps.get_model('papers','Dataset').objects.filter(conditionset=self).distinct()

    def link_detail(self):
        return ', '.join([c.link_detail() for c in self.conditions.order_by('type__name')])
    link_detail.allow_tags = True

    def link_edit(self):
        return '{<a href="%s">%s</a>}' % (reverse("admin:conditions_conditionset_change", args=(self.id,)), self)
    link_edit.allow_tags = True
