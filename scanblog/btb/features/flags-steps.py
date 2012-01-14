import re
from lettuce import *
from lettuce.django import django_url
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver

from scanning.models import Document

@step(u'document (\d+) has no flags')
def document_has_no_flags(step, doc_id):
    doc = Document.objects.get(pk=doc_id)
    doc.notes = []
    assert doc.notes.count() == 0

@step(u'I click the flag button')
def i_click_the_flag_button(step):
    world.browser.find_element_by_class_name('flag-top-button').click()

@step(u'I see the flag form')
def i_see_the_flag_form(step):
    world.browser.find_element_by_id('id_reason')

@step(u'I enter "([^"]*)" in the flag form')
def i_enter_text_in_the_flag_form(step, text):
    el = world.browser.find_element_by_id('id_reason')
    el.clear()
    el.send_keys(text)

@step(u'I see a flag confirmation')
def i_see_a_flag_confirmation(step):
    messages = world.browser.find_elements_by_class_name('message')
    for message in messages:
        if "moderator will review that" in message.text:
            return
    assert 0, "Confirmation not found."

@step(u'document (\d+) has a comment and no flags')
def document_has_a_comment_and_no_flags(step, doc_id):
    doc = Document.objects.get(pk=doc_id)
    assert doc.comments.count() > 0
    doc.notes = []

@step(u'I click the comment flag button')
def i_click_the_comment_flag_button(step):
    href = world.browser.find_element_by_class_name(
            'comments'
    ).find_element_by_class_name(
            'comment-flag'
    ).get_attribute('href')
    world.browser.get(href)
    
