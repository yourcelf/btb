from difflib import SequenceMatcher

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape

register = template.Library()

@register.simple_tag
def column_diff(text1, text2):
    text1 = escape(text1)
    text2 = escape(text2)
    out1 = mark_safe(text1)
    out2 = show_diff(text1, text2)
    return mark_safe(u"<tr class='columndiff'><td>{0}</td><td>{1}</td></tr>".format(
        out1.replace(u"\n", u"<br />"), out2.replace(u"\n", u"<br />")
    ))

@register.simple_tag
def simple_diff(text1, text2):
    out = show_diff(escape(text1), escape(text2))
    return mark_safe(out.replace("\n", "<br />"))

def show_diff(a, b):
    seqm = SequenceMatcher(None, a, b)
    output= []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            output.append(seqm.a[a0:a1])
        elif opcode == 'insert':
            output.append(u"<span class='inserted'>%s</span>" % seqm.b[b0:b1])
        elif opcode == 'delete':
            output.append(u"<span class='deleted'>%s</span>" % seqm.a[a0:a1])
        elif opcode == 'replace':
            output.append(u"<span class='deleted'>%s</span><span class='inserted'>%s</span>" % (seqm.a[a0:a1], seqm.b[b0:b1]))
    return u''.join(output)
