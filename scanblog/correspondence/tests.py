import json
from django.test import TestCase

from btb.tests import BtbLoginTestCase
from correspondence import utils
from correspondence.models import StockResponse

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
        self.assertEquals(
            utils.tex_escape('Line one\r\nLine two\r\nLine three'),
            'Line one\\\\\nLine two\\\\\nLine three'
        )

class TestStockResponses(BtbLoginTestCase):
    def test_get_stock_response(self):
        stock_responses = [
                ["Stock 1", "The answer to your question 1..."],
                ["Stock 2", "The answer to your question 2..."],
                ["Stock 3", "The answer to your question 3..."],
        ]
        for name, body in stock_responses:
            StockResponse.objects.create(name=name, body=body)

        res = self.client.get("/correspondence/stock_responses.json")
        self.assertEquals(res.status_code, 403)

        self.loginAs("reader")
        res = self.client.get("/correspondence/stock_responses.json")
        self.assertEquals(res.status_code, 403)

        self.loginAs("moderator")
        res = self.client.get("/correspondence/stock_responses.json")
        self.assertEquals(res.status_code, 200)
        self.assertEquals(json.loads(res.content), {
            'results': [
                {'id': 3, 'name': "Stock 3", 'body': "The answer to your question 3..."},
                {'id': 2, 'name': "Stock 2", 'body': "The answer to your question 2..."},
                {'id': 1, 'name': "Stock 1", 'body': "The answer to your question 1..."},
            ]
        })
