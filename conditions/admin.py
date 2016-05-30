from django.contrib import admin
from django import forms
from django.http import HttpResponse

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
    list_display = ('id', 'type', 'dose', 'conditionsets_str_list')
    list_filter = ['type__name']
    ordering = ('type__short_name', 'dose')
    fields = ['type', 'dose']
    search_fields = ('type__name', 'type__short_name', 'type__pubchem_name', 'type__chebi_name', 'type__pubchem_id', 'type__chebi_id', 'dose')
    raw_id_fields = ('type',)

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse(
                '<script type="text/javascript">window.close();</script>')
        return super(ConditionAdmin, self).response_change(request, obj)


class ConditionInline(admin.TabularInline):
    model = Condition
    ordering = ('dose',)
    extra = 0


class ConditionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'chebi_name', 'pubchem_name', 'conditions_str_list')
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

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse(
                '<script type="text/javascript">window.close();</script>')
        return super(ConditionTypeAdmin, self).response_change(request, obj)


class ConditionSetAdmin(ImprovedModelAdmin):
    list_display = ('__unicode__', 'papers_edit_link_list',)
    raw_id_fields = ('conditions',)
    search_fields = ('name', 'conditions__type__name', 'conditions__type__short_name', 'conditions__type__pubchem_name', 'conditions__type__chebi_name')
    ordering = ('conditions__type__short_name',)
    inlines = (DatasetInline,)

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse(
                '<script type="text/javascript">window.close();</script>')
        return super(ConditionSetAdmin, self).response_change(request, obj)


admin.site.register(Condition, ConditionAdmin)
admin.site.register(ConditionType, ConditionTypeAdmin)
admin.site.register(ConditionSet, ConditionSetAdmin)
