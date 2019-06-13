from django.db import models
from django.core.urlresolvers import reverse
from django.apps import apps
from django.db.models import Q

import re

from phenotypes.models import Phenotype
from libchebipy import ChebiEntity


class ConditionTypeGroup(models.Model):
    name = models.CharField(max_length=200)
    order = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        return self.name


class ConditionType(models.Model):
    name = models.CharField(max_length=200)
    other_names = models.TextField(blank=True, null=True)

    pubchem_id = models.PositiveIntegerField(blank=True, null=True, unique=True)
    pubchem_name = models.CharField(max_length=200, blank=True, null=True)

    chebi_id = models.PositiveIntegerField(blank=True, null=True, unique=True)
    chebi_name = models.CharField(max_length=200, blank=True, null=True)

    group = models.ForeignKey(ConditionTypeGroup, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['group', 'chebi_name', 'pubchem_name', 'name', 'other_names']

    def __str__(self):
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
                    s = re.findall(r'\d+', tid)
                    outdict[t.get_name()] = int(s[0])
            return outdict
        else:
            return ''

    def conditions(self):
        return Condition.objects.filter(type=self).order_by('dose')

    def conditions_str_list(self):
        return ', '.join([p.dose for p in self.conditions()])

    def conditions_edit_list(self):
        return ', '.join([p.link_edit() for p in self.conditions()])
    conditions_edit_list.allow_tags = True

    def phenotypes(self):
        return Phenotype.objects.filter(Q(dataset__conditionset__conditions__type=self) |
                                        Q(dataset__medium__conditions__type=self)).distinct()

    def phenotypes_link_list(self):
        return ', '.join([p.link_detail() for p in self.phenotypes()])
    phenotypes_link_list.allow_tags = True

    def papers(self):
        return apps.get_model('papers', 'Paper').objects\
            .filter(Q(dataset__conditionset__conditions__type=self) | Q(dataset__medium__conditions__type=self))\
            .exclude(latest_data_status__status__status_name='not relevant').distinct()

    def papers_link_list(self):
        return ', '.join([(u'%s' % p.link_detail()) for p in self.papers()])
    papers_link_list.allow_tags = True

    def datasets(self):
        return apps.get_model('datasets', 'Dataset').objects.\
            filter(Q(conditionset__conditions__type=self) | Q(medium__conditions__type=self))\
            .exclude(paper__latest_data_status__status__status_name='not relevant').distinct()

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("conditions:detail", args=(self.id,)), self)
    link_detail.allow_tags = True


class Condition(models.Model):
    type = models.ForeignKey(ConditionType)
    dose = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField(blank=True, null=True)
    modified_on = models.DateField(auto_now=True, null=True)

    class Meta:
        get_latest_by = 'modified_on'

    def __str__(self):
        if self.dose == 'standard':
            txt = u'%s' % self.type
        else:
            txt = u'%s [%s]' % (self.type, self.dose)
        return txt

    def conditionsets(self):
        return ConditionSet.objects.filter(conditions=self).all()

    def media(self):
        return Medium.objects.filter(conditions=self).all()

    def conditionsets_str_list(self):
        return ", ".join([p.link_edit() for p in self.conditionsets()])
    conditionsets_str_list.allow_tags = True

    def media_str_list(self):
        return ", ".join([p.link_edit() for p in self.media()])
    media_str_list.allow_tags = True

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("conditions:detail", args=(self.type.id,)), self)
    link_detail.allow_tags = True

    def link_edit(self):
        return '<a href="%s">%s</a>' % (reverse("admin:conditions_condition_change", args=(self.id,)), self.dose)
    link_edit.allow_tags = True


class ConditionSet(models.Model):

    systematic_name = models.CharField(max_length=1000, blank=True, null=True)
    common_name = models.CharField(max_length=200, blank=True, null=True)
    display_name = models.CharField(max_length=1000, blank=True, null=True)

    conditions = models.ManyToManyField(Condition, blank=True)
    description = models.TextField(blank=True, null=True)

    # def save(self, *args, **kwargs):
    #
    #     # Generate the systematic name
    #     conditions_list = [(u'%s' % condition) for condition in
    #                        self.conditions.order_by('type__group__order', 'type__chebi_name', 'type__pubchem_name',
    #                                                 'type__name').all()]
    #     self.systematic_name = u'%s' % ", ".join(conditions_list)
    #
    #     self.display_name = self.systematic_name
    #     if self.common_name:
    #         self.display_name = self.common_name
    #
    #     super(ConditionSet, self).save(*args, **kwargs)

    def __str__(self):
        if self.display_name:
            return self.display_name
        else:
            return ''

    def papers(self):
        return apps.get_model('papers', 'Paper').objects.filter(dataset__conditionset=self)\
            .exclude(latest_data_status__status__status_name='not relevant').distinct()

    def papers_link_list(self):
        return ', '.join([p.link_detail() for p in self.papers()])
    papers_link_list.allow_tags = True

    def papers_edit_link_list(self):
        return ', '.join([p.link_edit() for p in self.papers()])
    papers_edit_link_list.allow_tags = True

    def datasets(self):
        return apps.get_model('datasets', 'Dataset').objects.filter(conditionset=self)\
            .exclude(paper__latest_data_status__status__status_name='not relevant').distinct()

    def datasets_edit_link_list(self):
        str = '<ul>'
        str = str + '<li>'.join([d.link_edit() for d in self.datasets()])
        str = str + '</ul>'
        return str
    datasets_edit_link_list.allow_tags = True

    def phenotypes(self):
        return Phenotype.objects.filter(dataset__conditionset=self).distinct()

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("conditions:conditionset_detail", args=(self.id,)), self)
    link_detail.allow_tags = True

    def link_edit(self):
        return '{<a href="%s">%s</a>}' % (reverse("admin:conditions_conditionset_change", args=(self.id,)), self)
    link_edit.allow_tags = True


class Medium(models.Model):

    systematic_name = models.CharField(max_length=1000, blank=True, null=True)
    common_name = models.CharField(max_length=200, blank=True, null=True)
    display_name = models.CharField(max_length=1000, blank=True, null=True)

    conditions = models.ManyToManyField(Condition, blank=True)
    description = models.TextField(blank=True, null=True)

    # def save(self, *args, **kwargs):
    #
    #     # Generate the systematic name
    #     conditions_list = [(u'%s' % condition) for condition in
    #                        self.conditions.order_by('type__group__order', 'type__chebi_name', 'type__pubchem_name',
    #                                                 'type__name').all()]
    #     self.systematic_name = u'%s' % ", ".join(conditions_list)
    #
    #     self.display_name = self.systematic_name
    #     if self.common_name:
    #         self.display_name = self.common_name
    #
    #     super(Medium, self).save(*args, **kwargs)

    def __str__(self):
        if self.display_name:
            return self.display_name
        else:
            return ''

    def papers(self):
        return apps.get_model('papers', 'Paper').objects.filter(Q(dataset__medium=self) |
                                                                Q(dataset__control_medium=self))\
            .exclude(latest_data_status__status__status_name='not relevant').distinct()

    def papers_link_list(self):
        return ', '.join([p.link_detail() for p in self.papers()])
    papers_link_list.allow_tags = True

    def papers_edit_link_list(self):
        return ', '.join([p.link_edit() for p in self.papers()])
    papers_edit_link_list.allow_tags = True

    def datasets(self):
        return apps.get_model('datasets', 'Dataset').objects.filter(medium=self)\
            .exclude(paper__latest_data_status__status__status_name='not relevant').distinct()

    def datasets_edit_link_list(self):
        str = '<ul>'
        str = str + '<li>'.join([d.link_edit() for d in self.datasets()])
        str = str + '</ul>'
        return str
    datasets_edit_link_list.allow_tags = True

    def phenotypes(self):
        return Phenotype.objects.filter(dataset__medium=self).distinct()

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("conditions:medium_detail", args=(self.id,)), self)
    link_detail.allow_tags = True

    def link_edit(self):
        return '{<a href="%s">%s</a>}' % (reverse("admin:conditions_medium_change", args=(self.id,)), self)
    link_edit.allow_tags = True
