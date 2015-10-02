from django.contrib import admin

from papers.models import Paper, Dataset, Collection, Source, Status, Statusdata, Statustested


class StatusdataInline(admin.TabularInline):
    model = Statusdata
    extra = 0


class StatustestedInline(admin.TabularInline):
    model = Statustested
    extra = 0


class SourceAdmin(admin.ModelAdmin):
    model = Source
    list_display = ('__unicode__',)
    fields = ('sourcetype','link','person','date','release','acknowledge')


class CollectionAdmin(admin.ModelAdmin):
    model = Collection
    list_display = ('__unicode__',)



class DatasetInline(admin.TabularInline):
    model = Dataset
    fields = ('id','conditionset', 'phenotype', 'collection','tested_num','tested_list_published','tested_source','changetestedsource_link','data_measured','data_published','data_available','data_source','changedatasource_link','notes')
    #raw_id_fields = ('conditionset', 'phenotype', 'tested_source', 'data_source')
    readonly_fields = ('id', 'changetestedsource_link','changedatasource_link')
    extra = 0


class PaperAdmin(admin.ModelAdmin):
    list_per_page = 1000
    list_display = ('pmid', 'user', '__unicode__', 'DatasetList')
    list_filter = ['pub_date', 'last_author']
    ordering = ('pub_date', 'last_author', 'first_author')
    fields = [('user',), ('first_author', 'last_author','pub_date', 'pmid'), ('notes', 'private_notes'), ]
    inlines = (StatusdataInline, StatustestedInline, DatasetInline,)
    search_fields = ('pmid', 'first_author', 'last_author')

    def save_model(self, request, obj, form, change):
        if not obj.user:
            obj.user = request.user
        obj.save()

    def DatasetList(self, obj):
        list = ""
        for d in Dataset.objects.filter(paper=obj.id):
            list += '%s  ' % (unicode(d))
        return list


class StatusAdmin(admin.ModelAdmin):
    inlines = (StatusdataInline, StatustestedInline)



admin.site.register(Paper, PaperAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(Collection, CollectionAdmin)
