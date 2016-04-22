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
    fields = ('sourcetype', 'link', 'person', 'date', 'release', 'acknowledge')


class CollectionAdmin(admin.ModelAdmin):
    model = Collection
    list_display = ('__unicode__',)


class DatasetInline(admin.TabularInline):
    model = Dataset
    fields = ('id', 'conditionset', 'phenotype', 'collection', 'tested_num', 'tested_list_published', 'tested_source',
              'changetestedsource_link', 'data_measured', 'data_published', 'data_available', 'data_source',
              'changedatasource_link', 'notes')
    raw_id_fields = ('conditionset', 'phenotype', 'tested_source', 'data_source')
    readonly_fields = ('id', 'changetestedsource_link', 'changedatasource_link')
    extra = 0


class PaperAdmin(admin.ModelAdmin):
    list_per_page = 1000
    list_display = ('pmid', 'user', '__unicode__', 'DatasetList',
                    'latest_data_status_name', 'latest_tested_status_name')
    list_filter = ['pub_date', 'last_author']
    ordering = ('pub_date', 'last_author', 'first_author',)
    fields = [('user',), ('first_author', 'last_author', 'pub_date', 'pmid'), ('notes', 'private_notes'), ]
    inlines = (StatusdataInline, StatustestedInline, DatasetInline,)
    search_fields = ('pmid', 'first_author', 'last_author')

    def save_model(self, request, obj, form, change):
        pass

    def save_related(self, request, form, formsets, change):
        paper = form.instance

        # If creating a new paper, just save the instance first
        if paper.pk is None:
            super(PaperAdmin, self).save_model(request, paper, form, change)

        # When the paper exists, first save the related data, then update the paper itself
        form.save_m2m()
        for formset in formsets:
            self.save_formset(request, form, formset, change=change)
        if not paper.user:
            paper.user = request.user
        if paper.statusdata_set.all():
            paper.latest_data_status = paper.statusdata_set.latest()
        else:
            paper.latest_data_status = None
        if paper.statustested_set.all():
            paper.latest_tested_status = paper.statustested_set.latest()
        else:
            paper.latest_tested_status = None
        super(PaperAdmin, self).save_model(request, paper, form, change)


    def DatasetList(self, obj):
        list = ""
        for d in Dataset.objects.filter(paper=obj.id):
            list += '%s  ' % (unicode(d))
        return list


class StatusAdmin(admin.ModelAdmin):
    list_display = ('status_name',)
    ordering = ('status_name',)


admin.site.register(Paper, PaperAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(Collection, CollectionAdmin)
