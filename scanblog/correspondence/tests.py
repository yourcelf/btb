from django.test import TestCase

from correspondence import utils

class TextLatexCompilation(TestCase):
    def test_escape_tex(self):
        self.assertEquals(
            utils.tex_escape('Line one\nLine two\nLine three'),
            'Line one\\\\\nLine two\\\\\nLine three'
        )
        self.assertEquals(
            utils.tex_escape('Line one\n\nLine three'),
            'Line one\\\\\n~\\\\\nLine three'
        )
