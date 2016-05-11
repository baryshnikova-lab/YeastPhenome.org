from django.contrib import admin
from django.db import models
from mptt.admin import MPTTModelAdmin
from phenotypes.models import MutantType, Observable2, Phenotype


class Observable2Admin(MPTTModelAdmin):
    list_per_page = 1000
    list_display = ['name', 'definition']
    search_fields = ['name', ]

    def save_model(self, request, obj, form, change):
        obj.save()
        if not obj.ancestry:
            obj.ancestry = '%s%03d.' % (obj.parent.ancestry, obj.id)
            obj.save()

    def to_field_allowed(self, request, to_field):
        """This is a littel hacky, but setting to_field='ancestry' in
        Observable2.parent broke MPTTModel.get_children() when
        generating the graphics.  So until I can figure out a better
        way..."""

        if 'ancestry' == to_field:
            return True
        return super(MPTTModelAdmin,self).to_field_allowed(request, to_field)
    class Media:
        js={'ancestor.js'};


class MutantTypeAdmin(admin.ModelAdmin):
    list_filter = ['name']
    list_display = ['id', 'name', 'definition']
    ordering = ['name']


class PhenotypeAdmin(admin.ModelAdmin):
    list_per_page = 1000
    list_display = ['observable2_name', 'name', 'reporter', 'papers_edit_link_list']
    ordering = ['observable2__ancestry']
    search_fields = ['name', ]


admin.site.register(Phenotype, PhenotypeAdmin)
admin.site.register(MutantType, MutantTypeAdmin)
admin.site.register(Observable2, Observable2Admin)
