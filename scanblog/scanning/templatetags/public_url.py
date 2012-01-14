from django import template
from scanning.models import public_url

register = template.Library()
register.filter('public_url', public_url)

