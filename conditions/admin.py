from django.contrib import admin

from conditions.models import ConditionSet, Condition, ConditionType
from papers.models import Dataset


class DatasetInline(admin.TabularInline):
    model = Dataset
    fields = ('conditionset', 'phenotype', 'collection','tested_num','tested_list_published','tested_source','changetestedsource_link','data_measured','data_published','data_available','data_source','changedatasource_link','notes')
    raw_id_fields = ('conditionset', 'phenotype', 'tested_source', 'data_source')
    readonly_fields = ('changetestedsource_link','changedatasource_link')
    extra = 0


class ConditionAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'type', 'dose', 'condition_sets')
    list_filter = ['type__name']
    ordering = ('type__short_name', 'dose')
    fields = ['name', 'type', 'dose']
    search_fields = ('type__name', 'type__short_name')


class ConditionTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'group', 'external_link')
    list_filter = ['group']
    ordering = ('name',)
    radio_fields = {'group': admin.VERTICAL}
    search_fields = ('name', 'short_name')


class ConditionSetAdmin(admin.ModelAdmin):
    list_display = ('__unicode__', 'papers',)
    list_filter = ['conditions__type__short_name']
    filter_horizontal = ['conditions']
    search_fields = ('conditions__type__name', 'conditions__type__short_name',)
    ordering = ('conditions__type__short_name',)
    inlines = (DatasetInline,)
    class Media:
        js={'foo.js'}

admin.site.register(Condition, ConditionAdmin)
admin.site.register(ConditionType, ConditionTypeAdmin)
admin.site.register(ConditionSet, ConditionSetAdmin)
