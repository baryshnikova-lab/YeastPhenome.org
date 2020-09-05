from django.contrib import admin
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponse
from django.db.models import Min

import re

from pubchempy import Compound
from libchebipy import ChebiEntity

from conditions.models import ConditionSet, Condition, ConditionType, Medium, Tag
from common.admin_util import ImprovedTabularInline, ImprovedModelAdmin


class TagAdmin(ImprovedModelAdmin):
    list_per_page = 50
    list_display = ['name', 'description']
    search_fields = ['name', 'description']
    fields = ('name', 'description', 'conditiontypes_edit_link_list')
    readonly_fields = ('conditiontypes_edit_link_list', )
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


class ConditionAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(ConditionAdminForm, self).clean()
        dose = cleaned_data.get('dose')
        if dose is None or dose == '':
            self.add_error('dose', 'If unsure about the value, insert "unknown".')
        return cleaned_data


class ConditionAdmin(ImprovedModelAdmin):
    form = ConditionAdminForm
    list_display = ('id', 'type', 'dose', 'conditionsets_str_list', 'media_str_list')
    list_filter = ['type__name']
    ordering = ('type__name', 'dose')
    fields = ['type', 'dose', 'description']
    search_fields = ('type__name', 'type__other_names', 'type__pubchem_name', 'type__chebi_name',
                     'type__pubchem_id', 'type__chebi_id', 'dose')
    raw_id_fields = ('type',)

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse(
                '<script type="text/javascript">window.opener.location.reload(); window.close();</script>')
        return super(ConditionAdmin, self).response_change(request, obj)


class ConditionInline(ImprovedTabularInline):
    model = Condition
    fields = ('id', 'admin_change_link')
    readonly_fields = ('id', 'admin_change_link')
    ordering = ('dose',)
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        if obj:
            self.parent_obj_id = obj.id
        return super(ConditionInline, self).get_formset(request, obj, **kwargs)

    def admin_change_link(self, obj):
        if obj.id:
            return '<a href="%s?_popup=1" onclick="return showAddAnotherPopup(this);">%s</a>' \
                   % (reverse("admin:conditions_condition_change", args=(obj.id,)), obj.dose)
        else:
            return '<a href="%s?_popup=1&type=%s" onclick="return showAddAnotherPopup(this);">Create new</a>' \
                   % (reverse("admin:conditions_condition_add"), self.parent_obj_id)
    admin_change_link.allow_tags = True


class ConditionTypeAdmin(ImprovedModelAdmin):
    list_display = ('name', 'chebi_name', 'pubchem_name', 'conditions_edit_list', 'tags_edit_list')
    ordering = ('name',)
    search_fields = ('name', 'other_names', 'chebi_id', 'chebi_name', 'pubchem_id', 'pubchem_name')
    fields = ('name', 'other_names', 'tags', 'description', 'chebi_id', 'chebi_name', 'pubchem_id', 'pubchem_name')
    readonly_fields = ('chebi_name', 'pubchem_name',)
    raw_id_fields = ('tags',)
    inlines = (ConditionInline,)

    def save_model(self, request, obj, form, change):
        if form.cleaned_data['chebi_id']:
            chebi_id = form.cleaned_data['chebi_id']
            chebi_comb = ChebiEntity('CHEBI:'+str(chebi_id))
            parent_id = chebi_comb.get_parent_id()
            if parent_id:
                s = re.findall(r'\d+', parent_id)
                chebi_id = int(s[0])
                chebi_comb = ChebiEntity('CHEBI:'+str(chebi_id))
            obj.chebi_id = chebi_id
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
    list_display = ('id', 'display_name', 'papers_edit_link_list', )
    raw_id_fields = ('conditions', )
    search_fields = ('systematic_name', 'common_name',
                     'conditions__type__name', 'conditions__type__other_names',
                     'conditions__type__pubchem_name', 'conditions__type__chebi_name')
    ordering = ('id', 'display_name', )

    fields = ('systematic_name', 'common_name', 'display_name',
              'conditions', 'description', 'datasets_edit_link_list', )
    readonly_fields = ('systematic_name', 'display_name', 'datasets_edit_link_list', )

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse(
                '<script type="text/javascript">window.opener.location.reload(); window.close();</script>')
        return super(ConditionSetAdmin, self).response_change(request, obj)

    def save_model(self, request, obj, form, change):

        obj.save()
        form.save_m2m()

        conditions_list = [(u'%s' % condition) for condition in
                           obj.conditions.annotate(tags_order=Min('type__tags__order')).\
                               order_by('tags_order', 'type__chebi_name', 'type__pubchem_name','type__name').all()]
        conditions_str = ", ".join(conditions_list)
        obj.systematic_name = conditions_str[:1000] if len(conditions_str) > 1000 else conditions_str

        obj.display_name = obj.systematic_name
        if obj.common_name:
            obj.display_name = obj.common_name

        obj.save()


class MediumAdmin(ImprovedModelAdmin):
    list_display = ('id', 'display_name', 'papers_edit_link_list',)
    raw_id_fields = ('conditions',)
    search_fields = ('systematic_name', 'common_name',
                     'conditions__type__name', 'conditions__type__other_names',
                     'conditions__type__pubchem_name', 'conditions__type__chebi_name')
    ordering = ('id', 'display_name', )

    fields = ('systematic_name', 'common_name', 'display_name',
              'conditions', 'description', 'datasets_edit_link_list_top50', )
    readonly_fields = ('systematic_name', 'display_name', 'datasets_edit_link_list_top50', )

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse(
                '<script type="text/javascript">window.opener.location.reload(); window.close();</script>')
        return super(MediumAdmin, self).response_change(request, obj)

    def save_model(self, request, obj, form, change):

        obj.save()
        form.save_m2m()

        conditions_list = [(u'%s' % condition) for condition in
                           obj.conditions.annotate(tags_order=Min('type__tags__order')).\
                               order_by('tags_order', 'type__chebi_name', 'type__pubchem_name', 'type__name').all()]
        conditions_str = ", ".join(conditions_list)
        obj.systematic_name = conditions_str[:1000] if len(conditions_str) > 1000 else conditions_str

        obj.display_name = obj.systematic_name
        if obj.common_name:
            obj.display_name = obj.common_name

        obj.save()


admin.site.register(Tag, TagAdmin)
admin.site.register(Condition, ConditionAdmin)
admin.site.register(ConditionType, ConditionTypeAdmin)
admin.site.register(ConditionSet, ConditionSetAdmin)
admin.site.register(Medium, MediumAdmin)
