from django.contrib import admin
from django import forms

from pubchempy import Compound
from libchebipy import ChebiEntity

from conditions.models import ConditionSet, Condition, ConditionType
from papers.models import Dataset
from common.admin_util import ImprovedTabularInline, ImprovedModelAdmin


class ConditionAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(ConditionAdminForm, self).clean()
        dose = cleaned_data.get('dose')
        if dose is None or dose == '':
            self.add_error('dose', "If unsure about the value, insert <unknown>.")
        super(ConditionAdminForm, self).clean()


class DatasetInline(ImprovedTabularInline):
    model = Dataset
    fields = ('paper', 'conditionset', 'phenotype', 'collection',
              'tested_num', 'tested_list_published', 'tested_source',
              'data_measured', 'data_published', 'data_available', 'data_source', 'notes')
    raw_id_fields = ('paper', 'conditionset', 'phenotype', 'tested_source', 'data_source')
    extra = 0


class ConditionAdmin(ImprovedModelAdmin):
    form = ConditionAdminForm
    list_display = ('id', 'type', 'dose', 'condition_sets')
    list_filter = ['type__name']
    ordering = ('type__short_name', 'dose')
    fields = ['type', 'dose']
    search_fields = ('type__name', 'type__short_name')
    raw_id_fields = ('type',)


class ConditionInline(admin.TabularInline):
    model = Condition
    ordering = ('dose',)
    extra = 0


class ConditionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'chebi_name', 'pubchem_name', 'conditions')
    list_filter = ['group']
    ordering = ('name',)
    radio_fields = {'group': admin.VERTICAL}
    search_fields = ('name', 'short_name', 'chebi_id', 'chebi_name', 'pubchem_id', 'pubchem_name')
    fields = ('name', 'short_name', 'group', 'description', 'chebi_id', 'chebi_name', 'pubchem_id', 'pubchem_name')
    readonly_fields = ('chebi_name', 'pubchem_name',)
    inlines = (ConditionInline,)

    def save_model(self, request, obj, form, change):
        if form.cleaned_data['chebi_id']:
            chebi_comb = ChebiEntity('CHEBI:'+str(form.cleaned_data['chebi_id']))
            obj.chebi_name = chebi_comb.get_name()
        else:
            obj.chebi_name = None
        if form.cleaned_data['pubchem_id']:
            comp = Compound.from_cid(form.cleaned_data['pubchem_id'])
            obj.pubchem_name = comp.synonyms[0]
        else:
            obj.pubchem_name = None
        obj.save()


class ConditionSetAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'papers',)
    list_filter = ['conditions__type__short_name']
    filter_horizontal = ['conditions']
    search_fields = ('name', 'conditions__type__name', 'conditions__type__short_name',)
    ordering = ('conditions__type__short_name',)
    inlines = (DatasetInline,)

    class Media:
        js = ('conditionset.js',)

admin.site.register(Condition, ConditionAdmin)
admin.site.register(ConditionType, ConditionTypeAdmin)
admin.site.register(ConditionSet, ConditionSetAdmin)
