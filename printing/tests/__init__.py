import os
import re
import json
import difflib
import unittest

from print_mail import collate_letters, collate_postcards
from click2mail import Click2MailBatch

MAILDIR = os.path.join(os.path.dirname(__file__), "mailing_dir")

class Clic2MailXMLTest(unittest.TestCase):
    def _get_manifest(self):
        filename = os.path.join(os.path.dirname(__file__),
                "mailing_dir", "manifest.json")
        with open(filename) as fh:
            data = json.load(fh)
        return data

    def assertBigTextEquals(self, desired, actual):
        diffs = "".join(difflib.context_diff(desired, actual))
        self.assertEquals(desired, actual, "Unequal strings. Diff:\n" + diffs)

    def test_collate_postcards(self):
        manifest = self._get_manifest()
        files, vals, page = collate_postcards(manifest["postcards"], 1)
        self.assertEquals(files, [
            os.path.join("postcards", "waitlist.pdf")
        ])
        self.assertEquals(vals, [{'endingPage': 1,
            'recipient': {'address1': u'#69725379',
                          'address2': u'367 Cherry Tree Lane',
                          'city': u'City Name',
                          'name': u'Franti\u0161ek Loukianos',
                          'state': u'NE',
                          'zip': u'05397'},
            'sender': {'address1': u'PO Box 123',
                       'city': u'Cambridge',
                       'name': u'Blog Crew',
                       'state': u'MA',
                       'zip': u'12345'},
            'startingPage': 1,
            'type': 'postcard'}
        ])
        self.assertEquals(page, 2)

    def test_collate_letters(self):
        manifest = self._get_manifest()
        files, vals, page = collate_letters(MAILDIR, manifest["letters"], 1)
        self.assertEquals(files, [
            os.path.join(MAILDIR, "letters", "frantisek-loukianos-letter10.pdf"),
            os.path.join(MAILDIR, "letters", "frantisek-loukianos-consent_form13.pdf"),
            os.path.join(MAILDIR, "letters", "frantisek-loukianos-comments18.pdf"),
            os.path.join(MAILDIR, "letters", "valentin-rosemary-printout9.pdf"),
            os.path.join(MAILDIR, "letters", "valentin-rosemary-first_post16.pdf"),
        ])
        self.assertEquals(vals, [
            {
                'startingPage': 1,
                'endingPage': 13,
                'recipient': {
                    'city': u'City Name',
                    'name': u'Franti\u0161ek Loukianos',
                    'zip': u'05397',
                    'address1': u'#69725379',
                    'address2': u'367 Cherry Tree Lane',
                    'state': u'NE'
                },
                'sender': {
                    'address1': u'PO Box 123',
                    'state': u'MA',
                    'name': u'Blog Crew',
                    'zip': u'12345',
                    'city': u'Cambridge'
                },
                'type': 'letter'
            }, {
                'startingPage': 14,
                'endingPage': 18,
                'recipient': {
                    'city': u'City Name',
                    'name': u'Valentin Rosemary',
                    'zip': u'70903',
                    'address1': u'#74271666',
                    'address2': u'642 Cherry Tree Lane',
                    'state': u'WY'
                },
                'sender': {
                    'address1': u'PO Box 123',
                    'state': u'MA',
                    'name': u'Other Crew',
                    'zip': u'12345',
                    'city': u'Cambridge'
                },
                'type': 'letter'
            }
        ])
        self.assertEquals(page, 19)
    
    def test_click2mail_xml(self):
        manifest = self._get_manifest()
        lfiles, ljobs, lpage = collate_letters(MAILDIR, manifest["letters"], 1)
        pfiles, pjobs, ppage = collate_postcards(manifest["postcards"], lpage)

        batch = Click2MailBatch(
                username="username",
                password="password",
                filename="/tmp/somefile.pdf",
                jobs=ljobs + pjobs,
                staging=True)
        xml = batch.build_batch_xml()
        with open(os.path.join(MAILDIR, "correct_xml.xml")) as fh:
            expected_xml = fh.read()
        self.assertBigTextEquals(expected_xml, xml)

class TestMultiLineAddressBehavior(unittest.TestCase):
    def test_multi_line_addresses(self):
        jobs = [{
            "startingPage": 0,
            "endingPage": 1,
            "type": "letter",
            "recipients": [{
                "name": "Kyle De Wolf",
                "address1": "14966-052",
                "address2": "Low Security Correctional Institution Allenwood",
                "address3": "PO Box 1000",
                "city": "White Deer",
                "state": "PA",
                "zip": "17887"
            }, {
                "name": "Marcus T. Rogers Jr",
                "address1": "#377571",
                "address2": "John Burke Correctional Center",
                "address3": "P.O. Box 900",
                "city": "Waupun",
                "state": "WI",
                "zip": "53963"
            }, {
                "name": "Craig Middlemass",
                "address1": "#16988-014 Creek B",
                "address2": "Federal Correctional Institution",
                "address3": "P.O. Box 7007",
                "city": "Marianna",
                "state": "FL",
                "zip": "32447-7007"
            }, {
                "name": "Johnny E. Mahaffey",
                "address1": "32363",
                "address2": "Wateree 193",
                "address3": "4460 Broad River Rd.",
                "city": "Columbia",
                "state": "SC",
                "zip": "29210-4012"
            }]
        }]
        batch = Click2MailBatch(
                username="username",
                password="password",
                filename="/tmp/somefile.pdf",
                jobs=jobs,
                staging=True)
        print(batch.build_batch_xml())

if __name__ == "__main__":
    unittest.main()
