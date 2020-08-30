from django.contrib import admin
from django.http import HttpResponse

from phenotypes.models import MutantType, Observable, Phenotype, Measurement, Tag
from common.admin_util import ImprovedModelAdmin


class ObservableAdmin(ImprovedModelAdmin):
    list_per_page = 50
    list_display = ['name', 'description', 'tags_str_list', 'papers_str_list']
    search_fields = ['name', 'description', 'tags__name']
    fields = ('name', 'description', 'tags', 'phenotypes_edit_link_list', 'datasets_edit_link_list', )
    readonly_fields = ('phenotypes_edit_link_list', 'datasets_edit_link_list', )
    raw_id_fields = ('tags',)
    ordering = ['name']

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse(
                '<script type="text/javascript">window.opener.location.reload(); window.close();</script>')
        return super(ObservableAdmin, self).response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        if request.GET.get('_popup') == '1':
            return HttpResponse('<script type="text/javascript">window.opener.location.reload(); window.close();</script>')
        return super(ObservableAdmin, self).response_add(request, obj, post_url_continue)


class TagAdmin(ImprovedModelAdmin):
    list_per_page = 50
    list_display = ['name', 'description', 'observables_str_list']
    search_fields = ['name', 'description']
    fields = ('name', 'description', 'observables_edit_link_list')
    readonly_fields = ('observables_edit_link_list', )
    ordering = ['name']

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse(
                '<script type="text/javascript">window.opener.location.reload(); window.close();</script>')
        return super(TagAdmin, self).response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        if request.GET.get('_popup') == '1':
            return HttpResponse('<script type="text/javascript">window.opener.location.reload(); window.close();</script>')
        return super(TagAdmin, self).response_add(request, obj, post_url_continue)


class MutantTypeAdmin(admin.ModelAdmin):
    list_filter = ['name']
    list_display = ['id', 'name', 'definition']
    ordering = ['name']


class PhenotypeAdmin(admin.ModelAdmin):
    list_per_page = 50
    list_display = ['name', 'observable_name', 'reporter', 'papers_edit_link_list']
    search_fields = ['name', 'description', 'observable__name']
    fields = ('name', 'description', 'observable', 'reporter', 'measurement',
              'datasets_edit_link_list', 'phenotype_siblings_edit_link_list')
    raw_id_fields = ('measurement', 'observable', )
    readonly_fields = ('datasets_edit_link_list', 'phenotype_siblings_edit_link_list')

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse(
                '<script type="text/javascript">window.opener.location.reload(); window.close();</script>')
        return super(PhenotypeAdmin, self).response_change(request, obj)


class MeasurementAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description']
    ordering = ['id']
    fields = ('name', 'description', 'phenotypes_edit_link_list')
    readonly_fields = ('phenotypes_edit_link_list', )


admin.site.register(Phenotype, PhenotypeAdmin)
admin.site.register(MutantType, MutantTypeAdmin)
admin.site.register(Observable, ObservableAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Measurement, MeasurementAdmin)
