import re
import os

for root, dirs, files in os.walk(os.path.abspath(os.path.dirname(__file__))):
    for fn in files:
        if fn.endswith(".swp"):
            continue
        path = os.path.join(root, fn)
        with open(path) as fh:
            txt = fh.read()
            # Look for problems with lacking i18n
            if "i18n" not in txt and "trans" in txt:
                print "Trans w/o i18n", path

            # Look for old style url invocations
            match = re.search(r"""(\{\%\s*url\s+\w+)""", txt)
            if match:
                print "Old style url", path

            # Look for dotted lookups inside blocktrans
            for match in re.finditer(
                    r"""\{\%\s*blocktrans\s*\%\}((.(?!\{\%\s*endblocktrans\s*\%\}))*)\{\%\s*endblocktrans\s*\%\}""",
                    txt, re.DOTALL):
                blocktrans = match.group(1)
                match = re.search(r"""(\{\{.*[\.].*\}\})""", blocktrans)
                if match:
                    print "bad blocktrans lookup", path

            # Look for blocktrans tags with variables missing 'with' or 'count'.
            if re.search(r"""\{\% blocktrans (?!(with |count |\%\}))""", txt):
                print "blocktrans missing with", path
                
            # Look for tabs
            if "\t" in txt:
                print "has tab characters", path

            # Look for blocks and variables inside {% trans "" %} tags
            for match in re.finditer(r"""\{\% trans ((.(?!\%\}))*) \%\}""", txt):
                if re.search("[\{\}]+", match.group(1)):
                    print "tags in trans", path

