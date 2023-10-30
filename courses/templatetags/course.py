from django import template


register = template.Library()

@register.filter
def model_name(obj):
    '''
    Шаблонный тег для доступа к закрытому атрибуту _meta
    '''
    try:
        return obj._meta.model_name
    except AttributeError:
        return None
