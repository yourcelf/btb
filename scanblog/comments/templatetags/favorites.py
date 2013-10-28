from django import template
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.conf import settings

register = template.Library()

@register.simple_tag(takes_context=True)
def favorites(context, model, user=None):
    user = user or context['user']
    has_favorited = user.is_authenticated() and \
            model.favorite_set.filter(user=user).exists()
    return render_to_string("comments/_favorites.html", {
        'thing': model,
        'STATIC_URL': settings.STATIC_URL,
        'num_favorites': model.favorite_set.count(),
        'has_favorited': has_favorited,
        'user': user,
    })

