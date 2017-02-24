from django.contrib import admin
from django.core.urlresolvers import reverse
from django.db.models import ForeignKey
from django.http import HttpResponse

# import urllib
from django.utils.http import urlencode
from itertools import chain

from papers.models import Paper, Status, Statusdata, Statustested
from datasets.models import Dataset, Collection, Source
from common.admin_util import ImprovedTabularInline, ImprovedModelAdmin


class DatasetAdmin(ImprovedModelAdmin):
    model = Dataset
    fields = ('paper', 'conditionset', 'phenotype', 'collection',
              'tested_num', 'tested_list_published', 'tested_source',
              'data_measured', 'data_published', 'data_available', 'data_source',
              'notes')
    raw_id_fields = ('paper', 'conditionset', 'phenotype', 'tested_source', 'data_source')
    save_as = True

    def get_changeform_initial_data(self, request):
        initial = super(DatasetAdmin, self).get_changeform_initial_data(request)
        if 'tested_list_published' in initial:
            if initial['tested_list_published'] == 'False':
                initial['tested_list_published'] = False
            elif initial['tested_list_published'] == 'True':
                initial['tested_list_published'] = True
        return initial

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse('<script type="text/javascript">window.opener.location.reload(); window.close();</script>')
        return super(DatasetAdmin, self).response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        if request.GET.get('_popup') == '1':
            return HttpResponse('<script type="text/javascript">window.opener.location.reload(); window.close();</script>')
        return super(DatasetAdmin, self).response_add(request, obj, post_url_continue)


class DatasetInline(ImprovedTabularInline):
    model = Dataset
    fields = ('id', 'admin_change_link', 'has_data_in_db', 'make_a_copy_link')
    readonly_fields = ('id', 'admin_change_link', 'has_data_in_db', 'make_a_copy_link')
    extra = 0
    max_num = 5000

    def get_formset(self, request, obj=None, **kwargs):
        if obj:
            self.parent_obj_id = obj.id
        return super(DatasetInline, self).get_formset(request, obj, **kwargs)

    def admin_change_link(self, obj):
        if obj.id:
            return '<a href="%s?_popup=1" onclick="return showAddAnotherPopup(this);">%s</a>' \
                   % (reverse("admin:datasets_dataset_change", args=(obj.id,)), obj.admin_name())
        else:
            return '<a href="%s?_popup=1&paper=%s" onclick="return showAddAnotherPopup(this);">Create new</a>' \
                   % (reverse("admin:datasets_dataset_add"), self.parent_obj_id)
    admin_change_link.allow_tags = True

    def make_a_copy_link(self, obj):
        query_string = 'test'
        # query_dict = {'_popup': 1}
        flds = list(set(chain.from_iterable(
            (field.name, field.attname) if hasattr(field, 'attname') else (field.name,)
            for field in obj._meta.get_fields()
            if not (field.many_to_one and field.related_model is None)
        )))
        return flds
        # # flds = obj._meta.get_fields()
        # for f in flds:
        #     #     f_name = f.name
        #     #     if isinstance(f, ForeignKey):
        #     #         f_name += "_id"
        #     return f.name + str(getattr(obj, f))
        #     # query_string += f.name
        # #     # if f.name != 'id' and f_value != 'None':
        # #     #     query_string += "&" + f.name + "=" + f_value
        # #     #     query_dict[f.name] = f_value
        # # # query_string = urlencode(query_dict)
        # # # return '<a id="id_user" href="%s?%s" onclick="return showAddAnotherPopup(this);">Make a copy</a>' % (reverse("admin:datasets_dataset_add"), query_string)
        # # return query_string
    make_a_copy_link.allow_tags = True


class DatasetInlineTested(DatasetInline):
    fk_name = 'tested_source'
    verbose_name = 'Dataset'
    verbose_name_plural = 'Datasets with tested strains provided by this source'


class DatasetInlineData(DatasetInline):
    fk_name = 'data_source'
    verbose_name = 'Dataset'
    verbose_name_plural = 'Datasets with data provided by this source'


class StatusdataInline(admin.TabularInline):
    model = Statusdata
    extra = 0


class StatustestedInline(admin.TabularInline):
    model = Statustested
    extra = 0


class SourceAdmin(admin.ModelAdmin):
    model = Source
    list_display = ('id', 'sourcetype', 'link_or_person')
    fields = ('sourcetype', 'link', 'person', 'date', 'release', 'acknowledge')
    inlines = [DatasetInlineTested, DatasetInlineData]

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse(
                '<script type="text/javascript">window.close();</script>')
        return super(SourceAdmin, self).response_change(request, obj)


class CollectionAdmin(admin.ModelAdmin):
    model = Collection
    list_display = ('__str__',)


class PaperAdmin(admin.ModelAdmin):
    list_per_page = 1000
    list_display = ('pmid', 'user', '__str__', 'datasets_summary',
                    'latest_data_status_name', 'latest_tested_status_name')
    list_filter = ['pub_date', 'last_author']
    ordering = ('pub_date', 'last_author', 'first_author',)
    fields = [('user',), ('first_author', 'last_author', 'pub_date', 'pmid'), ('notes', 'private_notes'), ]
    inlines = (StatusdataInline, StatustestedInline, DatasetInline,)
    search_fields = ('pmid', 'first_author', 'last_author')

    class Media:
        css = {"all": ("hide_admin_original.css",)}

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

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse(
                '<script type="text/javascript">window.close();</script>')
        return super(PaperAdmin, self).response_change(request, obj)


class StatusAdmin(admin.ModelAdmin):
    list_display = ('status_name',)
    ordering = ('status_name',)


admin.site.register(Paper, PaperAdmin)
admin.site.register(Source, SourceAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(Dataset, DatasetAdmin)
