from django.contrib import admin
from models import Choice
from models import ChoiceAttribute


class ChoiceAttributeInline(admin.StackedInline):
    model = ChoiceAttribute
    extra = 1


class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('content_type', 'field_name', 'display', 'value', 'order')
    ordering = ('content_type', 'field_name', 'order')
    inlines = [ChoiceAttributeInline]

admin.site.register(Choice, ChoiceAdmin)
