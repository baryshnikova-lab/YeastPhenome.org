from django.contrib import admin

from pubchempy import Compound

from conditions.models import ConditionSet, Condition, ConditionType
from papers.models import Dataset


class DatasetInline(admin.TabularInline):
    model = Dataset
    fields = ('conditionset', 'phenotype', 'collection','tested_num','tested_list_published','tested_source','changetestedsource_link','data_measured','data_published','data_available','data_source','changedatasource_link','notes')
    raw_id_fields = ('conditionset', 'phenotype', 'tested_source', 'data_source')
    readonly_fields = ('changetestedsource_link', 'changedatasource_link')
    extra = 0


class ConditionAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'dose', 'condition_sets')
    list_filter = ['type__name']
    ordering = ('type__short_name', 'dose')
    fields = ['type', 'dose']
    search_fields = ('type__name', 'type__short_name')
    raw_id_fields = ('type',)


class ConditionInline(admin.TabularInline):
    model = Condition
    extra = 0


class ConditionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'group', 'pubchem_id')
    list_filter = ['group']
    ordering = ('name',)
    radio_fields = {'group': admin.VERTICAL}
    search_fields = ('name', 'short_name')
    fields = ('name', 'short_name', 'group', 'description', 'pubchem_id', 'pubchem_name')
    readonly_fields = ('pubchem_name',)
    inlines = (ConditionInline,)

    def save_model(self, request, obj, form, change):
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
