from django.contrib import admin
from django.contrib.admin.sites import site
from django.contrib.admin.widgets import ManyToManyRawIdWidget, ForeignKeyRawIdWidget
from django.core.urlresolvers import reverse
from django.utils.html import escape

from django.urls.exceptions import NoReverseMatch
from django.utils.text import Truncator

from django.http import HttpResponse

from django.forms.models import BaseInlineFormSet


class VerboseForeignKeyRawIdWidget(ForeignKeyRawIdWidget):

    # Django 1.11
    template_name = 'foreign_key_raw_id.html'

    # Django 1.10.5
    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        try:
            obj = self.rel.to._default_manager.using(self.db).get(**{key: value})
            change_url = reverse(
                "admin:%s_%s_change" % (obj._meta.app_label, obj._meta.object_name.lower()),
                args=(obj.pk,)
            )
            return '&nbsp;<strong><a href="%s?_popup=1" onclick="return showAddAnotherPopup(this);"">%s</a></strong>' % (change_url, escape(obj))
        except (ValueError, self.rel.to.DoesNotExist):
            return '???'


class VerboseManyToManyRawIdWidget(ManyToManyRawIdWidget):

    # Django 1.11
    template_name = 'many_to_many_raw_id.html'

    # Django 1.10.5
    def label_for_value(self, value):
        values = value.split(',')
        str_values = []
        key = self.rel.get_related_field().name
        for v in values:
            try:
                obj = self.rel.to._default_manager.using(self.db).get(**{key: v})
                x = (u'%s' % obj)
                change_url = reverse(
                    "admin:%s_%s_change" % (obj._meta.app_label, obj._meta.object_name.lower()),
                    args=(obj.pk,)
                )
                str_values += [
                    '<strong><a href="%s?_popup=1" onclick="return showAddAnotherPopup(this);">%s</a></strong>' % (
                    change_url, escape(x))]
            except self.rel.to.DoesNotExist:
                str_values += [u'???']
        return u', '.join(str_values)

    # Django 1.11
    def label_and_url_for_value(self, value):
        key = self.rel.get_related_field().name

        link_label = []
        link_url = []
        for v in value:
            try:
                obj = self.rel.model._default_manager.using(self.db).get(**{key: v})
            except (ValueError, self.rel.model.DoesNotExist):
                return '', ''

            try:
                url = reverse(
                    '%s:%s_%s_change' % (
                        self.admin_site.name,
                        obj._meta.app_label,
                        obj._meta.object_name.lower(),
                    ),
                    args=(obj.pk,)
                )
            except NoReverseMatch:
                url = ''    # Admin not registered for target model.

            link_label.append(Truncator(obj).words(14, truncate='...'))
            link_url.append(url)

        return zip(link_label, link_url), ''


class ImprovedTabularInline(admin.TabularInline):
    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in self.raw_id_fields:
            kwargs.pop("request", None)
            type = db_field.rel.__class__.__name__
            if type == "ManyToOneRel":
                kwargs['widget'] = VerboseForeignKeyRawIdWidget(db_field.rel, site)
            elif type == "ManyToManyRel":
                kwargs['widget'] = VerboseManyToManyRawIdWidget(db_field.rel, site)
            return db_field.formfield(**kwargs)
        return super(ImprovedTabularInline, self).formfield_for_dbfield(db_field, **kwargs)


class ImprovedModelAdmin(admin.ModelAdmin):

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name in self.raw_id_fields:
            kwargs.pop("request", None)
            type = db_field.rel.__class__.__name__
            if type == "ManyToOneRel":
                kwargs['widget'] = VerboseForeignKeyRawIdWidget(db_field.rel, site)
            elif type == "ManyToManyRel":
                kwargs['widget'] = VerboseManyToManyRawIdWidget(db_field.rel, site)
            return db_field.formfield(**kwargs)
        return super(ImprovedModelAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def response_change(self, request, obj):
        if request.GET.get('_popup') == '1':
            return HttpResponse(
                '<script type="text/javascript">window.opener.location.reload(); window.close();</script>')
        return super(ImprovedModelAdmin, self).response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        if request.GET.get('_popup') == '1':
            return HttpResponse('<script type="text/javascript">window.opener.location.reload(); window.close();</script>')
        return super(ImprovedModelAdmin, self).response_add(request, obj, post_url_continue)


class LimitedInlineFormSet(BaseInlineFormSet):

    def get_queryset(self):
        qs = super(BaseInlineFormSet, self).get_queryset()
        return qs[:100]
