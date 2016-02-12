import os
import re
from lxml import etree
from lxml.builder import E
import requests
import time

class Click2MailBatch(object):
    def __init__(self, username, password, filename, jobs, staging=True):
        self.username = username
        self.password = password
        self.filename = filename
        self.jobs = jobs
        self.base_url = u"https://{}batch.click2mail.com/v1/batches".format(
                "stage-" if staging else "")

    @classmethod
    def letter_options_xml(cls, **kwargs):
        return E("printProductionOptions", 
            E("documentClass", "Letter 8.5 x 11"),
            E("layout", "Address on Separate Page"),
            E("productionTime", "Next Day"),
            E("envelope", kwargs.get("envelope", "#10 Double Window")),
            E("color", "Black and White"),
            E("paperType", "White 24#"),
            E("printOption", "Printing both sides"),
            E("mailClass", "First Class"))

    @classmethod
    def postcard_options_xml(cls, **kwargs):
        return E("printProductionOptions",
            E("documentClass", "Postcard 3.5 x 5"),
            E("layout", "Single Sided Postcard"),
            E("productionTime", "Next Day"),
            E("envelope", ""),
            E("color", "Black and White"),
            E("paperType", "White Matte"),
            E("printOption", "Printing both sides"),
            E("mailClass", "First Class"))

    @classmethod
    def return_address_xml(cls):
        return E("returnAddress",
            E("name", "Between the Bars"),
            E("organization", ""),
            E("address1", "2885 Sanford Ave SW # 30428"),
            E("address2", ""),
            E("city", "Grandville"),
            E("state", "MI"),
            E("postalCode", "49418"),
        )

    @classmethod
    def recipient_xml(cls, recipient):
        parts = []
        for key in ("name", "organization", "address1", "address2", "address3",
                    "city", "state", "zip"):
            upkey = "postalCode" if key == "zip" else key
            parts.append(E(upkey, recipient.get(key, "")))
        parts.append(E("country", ""))
        return E("address", *parts)

    def build_batch_xml(self):
        jobs_els = []
        for job in self.jobs:
            if job['type'] == "postcard":
                print_options = self.postcard_options_xml()
            else:
                num_pages = job["endingPage"] - job["startingPage"] + 1
                envelope = "#10 Double Window" if num_pages <= 10 else "Flat Envelope"
                print_options = self.letter_options_xml(envelope=envelope)
            jobs_els.append(E("job",
                E("startingPage", str(job["startingPage"])),
                E("endingPage", str(job["endingPage"])),
                print_options,
                self.return_address_xml(),
                E("recipients", *[self.recipient_xml(r) for r in job["recipients"]]),
            ))
        
        xml = u'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        return xml + etree.tostring(E("batch",
            E("username", self.username),
            E("password", self.password),
            E("filename", os.path.basename(self.filename)),
            *jobs_els
        ), pretty_print=True)

    @classmethod
    def check_res(cls, res, desired_status=200):
        if res.status_code != desired_status:
            raise Exception("Bad status {}: {}".format(res.status_code, res.text))
        if not res.text.strip():
            return None
        try:
            root = etree.fromstring(res.text.encode('utf-8'))
        except Exception as e:
            print res.text
            raise
        results = {
            "id": root.xpath('//id/text()')[0],
            "hasErrors": "".join(root.xpath('//hasErrors/text()')),
            "status": "".join(root.xpath('//status/text()')),
            "completedAt": "".join(root.xpath('//completedAt/text()')),
            "createdAt": "".join(root.xpath('//createdAt/text()'))
        }
        if results['status'] and results["status"] != "0":
            raise Exception("Bad xml status {}: {}".format(results['status'], res.text))
        if results['hasErrors'] and results['hasErrors'] != "false":
            raise Exception("Has errors {}: {}".format(results['hasErrors'], res.text))
        return results

    def create_batch(self, dry=False):
        url = self.base_url
        print url
        if dry:
            print "POST", url
            self.batch_id = "<id>"
        else:
            res = requests.post(url, auth=(self.username, self.password))
            results = self.check_res(res, 201)
            self.batch_id = results["id"]

    def upload_batch_xml(self, dry=False):
        url = "{}/{}".format(self.base_url, self.batch_id)
        print "PUT", url
        xml = self.build_batch_xml()
        if dry:
            print xml
        else:
            res = requests.put(url, data=xml,
                    headers={"Content-Type": "application/xml"},
                    auth=(self.username, self.password))
            results = self.check_res(res)

    def upload_pdf(self, dry=False):
        with open(self.filename, 'rb') as fh:
            pdf = fh.read()
        url = "{}/{}".format(self.base_url, self.batch_id)
        print "PUT", url
        if dry:
            print "<%s bytes binary pdf data>" % len(pdf)
        else:
            res = requests.put(url, data=pdf,
                    headers={"Content-Type": "application/pdf"},
                    auth=(self.username, self.password))
            results = self.check_res(res)

    def submit_job(self, dry=False):
        url = "{}/{}".format(self.base_url, self.batch_id)
        print "POST", url
        if not dry:
            res = requests.post(url, auth=(self.username, self.password))
            results = self.check_res(res)

    def poll_job_complete(self, dry=False):
        url = "{}/{}".format(self.base_url, self.batch_id)
        print "GET polling", url
        if not dry:
            while True:
                res = requests.get(url, auth=(self.username, self.password))
                results = self.check_res(res, 201)
                if results['completedAt']:
                    print res.text
                    print "Done"
                    return True
                time.sleep(20)

    def run(self, dry=False):
        self.create_batch(dry)
        self.upload_batch_xml(dry)
        self.upload_pdf(dry)
        self.submit_job(dry)
        self.poll_job_complete(dry)
        return True


if __name__ == "__main__":
    batch = Click2MailBatch("a", "b", "doc.pdf", [
        {"startingPage": 0, "endingPage": 4, "recipient": ["John Dough", "12345", "Cherry tree lane", "PO Box OK", "This, DAT 12345"]},
        {"startingPage": 5, "endingPage": 9, "recipient": ["Jane Dough", "23456", "Oak tree lane", "PO Box 99", "This, OT 23456"]},
    ])

    print batch.build_batch_xml()
