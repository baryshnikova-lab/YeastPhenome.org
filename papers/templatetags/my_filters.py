from django import template

register = template.Library()


@register.filter(name='join_and_more', is_safe=True)
def join_and_more(qs, number_obj_to_show):
    l = len(qs)
    if l == 0:
        return ''
    elif l <= number_obj_to_show:
        return ", ".join((u'%s' % obj) for obj in qs)
    else:
        number_obj_remaining = l - number_obj_to_show
        return ", ".join((u'%s' % obj) for obj in qs[:number_obj_to_show-1]) + " ... (and " + str(number_obj_remaining) + " more)"
