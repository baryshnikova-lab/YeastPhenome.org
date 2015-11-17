from django.contrib import admin
from django.db import models
from mptt.admin import MPTTModelAdmin
from models import MutantType, Observable2, Phenotype


class Observable2Admin(MPTTModelAdmin):
    list_per_page = 1000
    list_display = ['name', 'definition']
    search_fields = ['name', ]

    def save_model(self, request, obj, form, change):
        obj.save()
        if not obj.ancestry:
            obj.ancestry = '%s%03d.' % (obj.parent.ancestry, obj.id)
            obj.save()

class MutantTypeAdmin(admin.ModelAdmin):
    list_filter = ['name']
    list_display = ['id', 'name', 'definition']
    ordering = ['name']


class PhenotypeAdmin(admin.ModelAdmin):
    list_per_page = 1000
    list_display = ['observable2_name', 'name', 'reporter', 'papers']
    ordering = ['observable2__ancestry']
    search_fields = ['name', ]


admin.site.register(Phenotype, PhenotypeAdmin)
admin.site.register(MutantType, MutantTypeAdmin)
admin.site.register(Observable2, Observable2Admin)
