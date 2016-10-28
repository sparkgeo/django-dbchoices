from decimal import Decimal

import django
from django.db import models
from django.contrib.contenttypes.models import ContentType
import django.db.models.options as model_options
from django.core.exceptions import ValidationError


try:
    from django import apps
    get_model = apps.apps.get_model
except ImportError:
    from django.db.models.loading import get_model


model_options.DEFAULT_NAMES = model_options.DEFAULT_NAMES + ('db_choices',)

o_model__init__ = django.db.models.Model.__init__
o_field__init__ = django.db.models.Field.__init__


def model_monkey_patch(self, *args, **kwargs):
    o_model__init__(self, *args, **kwargs)
    for field in self._meta.fields:
        if (hasattr(field, '_choices') and hasattr(field, 'dbchoices') and
                field.dbchoices is True):

            ct = ContentType.objects.get(app_label=self._meta.app_label,
                                         model=self._meta.model_name)
            choices = Choice.objects.choices(ct, field.name)
            field._choices = choices


def field_monkey_patch(self, *args, **kwargs):
    if 'dbchoices' in kwargs:
        self.dbchoices = kwargs['dbchoices']
        kwargs.pop('dbchoices')
    o_field__init__(self, *args, **kwargs)


django.db.models.Model.__init__ = model_monkey_patch
django.db.models.Field.__init__ = field_monkey_patch


class ChoiceManager(models.Manager):

    def _get_value_cast(self, content_type, field_name):
        if isinstance(content_type, (str, unicode,)):
            app, model = content_type.split('.')
            ModelClass = get_model(app_label=app, model_name=model)
        else:
            ModelClass = content_type.model_class
        field = ModelClass()._meta.get_field(field_name)
        field_type = field.get_internal_type()

        if field_type == 'IntegerField':
            cast = int
        elif field_type == 'FloatField':
            cast = float
        elif field_type == 'DecimalField':
            cast = Decimal
        else:
            cast = unicode

        return cast

    def _query(self, content_type, field_name, *args, **kwargs):
        qs = self.filter(field_name=field_name, *args, **kwargs)
        if isinstance(content_type, (str, unicode,)):
            app, model = content_type.split('.')
            p = {
                'content_type__app_label': app,
                'content_type__model': model
            }

            qs = qs.filter(**p)
        else:
            qs = qs.filter(content_type=content_type)
        return qs.order_by('order')

    def choices(self, content_type, field_name, *args, **kwargs):
        cs = self._query(content_type, field_name, *args, **kwargs)
        cast = self._get_value_cast(content_type, field_name)

        index = {}
        out = []
        n = 0
        for c in cs:
            if c.category is None or len(c.category) == 0:
                out.append((cast(c.value), c.display,))
                n += 1
            else:
                if c.category not in index:
                    index[c.category] = n
                    out.append((c.category, [],))
                    n += 1
                out[index[c.category]][1].append((cast(c.value), c.display,))
        return out

    def asdict(self, content_type, field_name, *args, **kwargs):
        cs = self._query(content_type, field_name, *args, **kwargs)
        cast = self._get_value_cast(content_type, field_name)
        return [{'value': cast(c.value),
                 'display': c.display,
                 'category': c.category,
                 'order': c.order,
                 'attributes': dict([(a.key, a.value)
                                     for a in c.attributes.all()]),
                 'field_name': c.field_name,
                 'model': '%s.%s' % (c.content_type.app_label,
                                     c.content_type.model)
                 }
                for c in cs]


class Choice(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    category = models.CharField(max_length=255, null=True, blank=True)
    field_name = models.CharField(max_length=100)
    display = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    order = models.IntegerField(default=0)

    objects = ChoiceManager()

    class Meta():
        unique_together = ('content_type', 'category', 'field_name', 'value', 'display')

    def clean(self, *args, **kwargs):
        try:
            m = self.content_type.model_class()
            m._meta.get_field(self.field_name)
        except AttributeError:
            import traceback
            traceback.print_exc()
            d = (
                self.field_name,
                self.content_type.app_label,
                self.content_type.model
            )
            raise ValidationError(
                'Field named "%s" doesn\'t exist in %s.%s' % d)

    def __unicode__(self):
        return self.display

class ChoiceAttribute(models.Model):
    choice = models.ForeignKey(Choice, related_name='attributes')
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=255)

    def __unicode__(self):
        return u'%s: %s' % (self.key, self.value)
