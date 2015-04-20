from django import template

register = template.Library()

@register.filter(name='join_and_more', is_safe=True)
def join_and_more(obj_list, number_obj_to_show):
    l = len(obj_list)
    if l == 0:
        return ''
    elif l <= number_obj_to_show:
        return ", ".join(unicode(obj) for obj in obj_list[:l])
    else:
        number_obj_remaining = l - number_obj_to_show
        return ", ".join(unicode(obj) for obj in obj_list[:number_obj_to_show-1]) + " ... (and " + str(number_obj_remaining) + " more)"
