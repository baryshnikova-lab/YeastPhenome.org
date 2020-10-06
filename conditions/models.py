from django.db import models
from django.core.urlresolvers import reverse
from django.apps import apps
from django.db.models import Q

import re

from phenotypes.models import Phenotype
from libchebipy import ChebiEntity


class Tag(models.Model):
    name = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField(max_length=1000, null=True, blank=True)
    order = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    def link_edit(self):
        return '<a href="%s">%s</a>' % (reverse("admin:conditions_tag_change", args=(self.id,)), self.name)
    link_edit.allow_tags = True

    def conditiontypes_edit_link_list(self):
        conditiontypes = self.conditiontype_set.order_by('name').all()
        html = '<ul>'
        html = html + '<li>'.join([c.link_edit() for c in conditiontypes[:50]])
        html = html + '</ul>'
        return html
    conditiontypes_edit_link_list.allow_tags = True


class ConditionType(models.Model):
    name = models.CharField(max_length=200)
    other_names = models.TextField(blank=True, null=True)

    pubchem_id = models.PositiveIntegerField(blank=True, null=True, unique=True)
    pubchem_name = models.CharField(max_length=200, blank=True, null=True)

    chebi_id = models.PositiveIntegerField(blank=True, null=True, unique=True)
    chebi_name = models.CharField(max_length=200, blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True)

    class Meta:
        ordering = ['chebi_name', 'pubchem_name', 'name', 'other_names']

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
            .exclude(latest_data_status__status__name='not relevant').distinct()

    def papers_link_list(self):
        return ', '.join([(u'%s' % p.link_detail()) for p in self.papers()])
    papers_link_list.allow_tags = True

    def datasets(self):
        return apps.get_model('papers', 'Dataset').objects.\
            filter(Q(conditionset__conditions__type=self) | Q(medium__conditions__type=self))\
            .exclude(paper__latest_data_status__status__name='not relevant').distinct()

    def tags_edit_list(self):
        return ', '.join([t.link_edit() for t in self.tags.all()])
    tags_edit_list.allow_tags = True

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("conditions:detail", args=(self.id,)), self)
    link_detail.allow_tags = True

    def link_edit(self):
        return '<a href="%s">%s</a>' % (reverse("admin:conditions_conditiontype_change", args=(self.id,)), self.name)
    link_edit.allow_tags = True


class Condition(models.Model):
    type = models.ForeignKey(ConditionType)
    dose = models.CharField(max_length=200, null=False, blank=False)
    description = models.TextField(blank=True, null=True)
    modified_on = models.DateField(auto_now=True, null=True)

    class Meta:
        get_latest_by = 'modified_on'

    def __str__(self):
        if self.dose in ['standard', 'unknown']:
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

    def __str__(self):
        if self.display_name:
            return self.display_name
        else:
            return ''

    # # Necessary to run database-wide updates of conditionset names
    # def save(self, *args, **kwargs):
    #
    #     # Generate the systematic name
    #     conditions_list = [(u'%s' % condition) for condition in
    #                        self.conditions.order_by('type__group__order', 'type__chebi_name', 'type__pubchem_name',
    #                                                 'type__name').all()]
    #     self.systematic_name = u'%s' % ", ".join(conditions_list)
    #     self.display_name = self.systematic_name
    #     if self.common_name:
    #         self.display_name = self.common_name
    #     super(ConditionSet, self).save(*args, **kwargs)

    def papers(self):
        ps = apps.get_model('papers', 'Paper').objects\
            .filter(Q(dataset__conditionset=self) | Q(dataset__control_conditionset=self))\
            .exclude(latest_data_status__status__name='not relevant').distinct()
        return ps

    def papers_all(self):
        ps = apps.get_model('papers', 'Paper').objects\
            .filter(Q(dataset__conditionset=self) | Q(dataset__control_conditionset=self)).distinct()
        return ps

    def papers_link_list(self):
        return ', '.join([p.link_detail() for p in self.papers()])
    papers_link_list.allow_tags = True

    def papers_edit_link_list(self):
        return ', '.join([p.link_edit() for p in self.papers_all()])
    papers_edit_link_list.allow_tags = True

    def datasets(self):
        return apps.get_model('datasets', 'Dataset').objects.filter(conditionset=self)\
            .exclude(paper__latest_data_status__status__name='not relevant').distinct()

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

    def __str__(self):
        if self.display_name:
            return self.display_name
        else:
            return ''

    def conditions_str_list(self):
        return ", ".join([str(c) for c in self.conditions.all()])

    def papers(self):
        ps = apps.get_model('papers', 'Paper').objects.filter(Q(dataset__medium=self) |
                                                                Q(dataset__control_medium=self))\
            .exclude(latest_data_status__status__name='not relevant').distinct()
        return ps

    def papers_all(self):
        ps = apps.get_model('papers', 'Paper').objects.filter(Q(dataset__medium=self) |
                                                              Q(dataset__control_medium=self)).distinct()
        return ps

    def paper_str_list(self):
        return ', '.join([str(p) for p in self.papers()])

    def papers_link_list(self):
        return ', '.join([p.link_detail() for p in self.papers()])
    papers_link_list.allow_tags = True

    def papers_edit_link_list(self):
        return ', '.join([p.link_edit() for p in self.papers_all()])
    papers_edit_link_list.allow_tags = True

    def datasets(self, num=None):
        qs = apps.get_model('datasets', 'Dataset').objects.filter(medium=self)\
            .exclude(paper__latest_data_status__status__name='not relevant').distinct()
        if num:
            qs = qs[:num]
        return qs

    def datasets_all(self, num=None):
        qs = apps.get_model('datasets', 'Dataset').objects.filter(medium=self).distinct()
        if num:
            qs = qs[:num]
        return qs

    def datasets_edit_link_list(self, num=None):
        qs = self.datasets_all(num=num)
        str = '<ul>'
        str = str + '<li>'.join([d.link_edit() for d in qs])
        str = str + '</ul>'
        return str
    datasets_edit_link_list.allow_tags = True

    def datasets_edit_link_list_top50(self):
        return self.datasets_edit_link_list(num=50)
    datasets_edit_link_list_top50.allow_tags = True

    def phenotypes(self):
        return Phenotype.objects.filter(dataset__medium=self).distinct()

    def link_detail(self):
        return '<a href="%s">%s</a>' % (reverse("conditions:medium_detail", args=(self.id,)), self)
    link_detail.allow_tags = True

    def link_edit(self):
        return '{<a href="%s">%s</a>}' % (reverse("admin:conditions_medium_change", args=(self.id,)), self)
    link_edit.allow_tags = True
