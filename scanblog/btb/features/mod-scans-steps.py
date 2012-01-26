import re
import os
import time
import datetime
from collections import defaultdict

from lettuce import *
from lettuce.django import django_url
from django.conf import settings
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException

from btblettuce import *

from scanning.models import Document

@step(u'I upload the scan "([^"]*)"')
def i_upload_the_scan(step, name):
    # Upload the file...
    world.browser.get(django_url("/scanning/add"))
    el = css("input[type=file]")
    el.send_keys(os.path.join(settings.SETTINGS_ROOT,
        "media", "test", "src", name))
    el.submit()
    # Wait for it...
    while "moderation/wait" in world.browser.current_url:
        try:
            el = css(".error")
            assert False, el.text
            break
        except NoSuchElementException:
            time.sleep(1)
    time.sleep(1) # 1 more for good measure.

@step(u'I see the split scan interface')
def i_see_the_split_scan_interface(step):
    assert world.browser.find_element_by_tag_name("h1").text == "Split Scan"

@step(u'the "([^"]*)" button is (disabled|enabled)')
def the_button_is_enabled(step, buttontext, abled):
    for el in csss("span"):
        if el.get_attribute("class") and el.text.startswith(buttontext):
            disabled = "disabled" in el.get_attribute("class")
            assert abled == "enabled" and not disabled or \
                   abled == "disabled" and disabled
            return
    assert 0, "Button with text %s not found." % buttontext

@step(u'I set the author as "([^"]*)"')
def i_set_the_author_as(step, name):
    css(".user-chooser-trigger").send_keys(name[0])
    css(".user-search").send_keys(name[1:])
    time.sleep(0.5)
    css(".user-search").send_keys(Keys.ENTER)

@step(u'I mark the pages according to their types')
def i_mark_the_pages_according_to_their_types(step):
    for hsh in step.hashes:
        selector = ".pagestatus.page-%s" % (int(hsh['page']) - 1)
        css(selector).click()
        time.sleep(0.1)
        # Must reacquire each time; as it rerenders, and elements go stale.
        choices = {}
        for el in csss(".page-type-choice"):
            if el.text.strip() == hsh['type']:
                el.click()
                break
        else:
            assert 0, "Can't find type '%s'" % hsh['type']

@step(u'documents for each part are created')
def documents_for_each_part_are_created(step):
    time.sleep(1) # wait for db to catch up
    types = defaultdict(list)
    for hsh in step.hashes:
        types[hsh['document']].append(int(hsh['pages']))
    docs = Document.objects.filter(
            created__gte=datetime.datetime.now() - datetime.timedelta(seconds=60),
    ).exclude(status="published")
    for doc in docs:
        types[doc.type].remove(doc.documentpage_set.count())
    for doctype, pagecount in types.iteritems():
        if pagecount:
            assert "Missing '%s' document with '%s' pages" % (doctype, pagecount)


@step(u'the license appears on the user detail page')
def license_appears_on_the_user_detail_page(step):
    user_id = int(css(".user-name").get_attribute("data-user-id"))
    world.browser.get(django_url("/moderation/#/users/%s" % user_id))
    assert len(css(".licenselist tr + tr").find_elements_by_tag_name("td")) == 2

@step(u'enter a pending scan for "([^"]*)"')
def enter_a_pending_scan_for_user(step, name):
    world.browser.get(django_url("/moderation/#/pending"))
    css(".user-chooser-trigger").send_keys(name[0])
    time.sleep(0.1)
    css(".user-search").send_keys(name[1:])
    time.sleep(0.1)
    css(".user-search").send_keys(Keys.ENTER)
    time.sleep(0.5)
    user_id = int(css(".user-id-raw").get_attribute("value"))
    scan_code = css(".reply-code").text
    world.scan_code = scan_code
    world.chosen_user_id = user_id
    time.sleep(1)

@step(u'I set the scan code')
def i_set_the_scan_code(step):
    css(".choose-code input").send_keys(world.scan_code)
    css(".choose-code input").send_keys(Keys.ENTER)
    css("h1").click() # arbitrary element to click to simulate 'blur'
    time.sleep(1)

@step(u'the pending scan is marked complete')
def the_pending_scan_is_marked_complete(step):
    ps = PendingScan.objects.get(code=world.scan_code)
    assert ps.scan != None
    assert ps.completed != None


@step(u'I see the document editing form with (\d+) documents')
def i_see_the_document_editing_form_with(step, num_docs):
    time.sleep(1)
    for el in csss("h2"):
        match = re.match("Document \d of (\d) \(\d pages?\)", el.text)
        if match:
            num = int(match.group(1))
            assert num == int(num_docs), "Expected %s; got %s" % (num_docs, num)
            return
    assert 0, "Document editing form not found."

@step(u'I enter the following into document (\d+)')
def i_enter_the_following_into_document(step, docnum):
    docs = csss('.edit-document')
    doc = docs[int(docnum) - 1]
    rows = csss(".form tr", doc)
    for hsh in step.hashes:
        for key in hsh.keys():
            for row in rows:
                if css("th", row).text.strip() == key:
                    for el in csss("input", row) + csss("select", row):
                        if el.is_displayed():
                            el.send_keys(hsh[key])
                            break
                    else:
                        assert 0, "No input for field '%s' found" % key
                    break
            else:
                assert 0, "Field with label '%s' not found." % key


@step(u'I select a highlight on the first page of document (\d+)')
def i_select_a_highlight_on_the_first_page_of_document(step, docnum):
    doc = csss('.edit-document')[int(docnum) - 1]
    el = css("canvas.page-image", doc)
    chain = ActionChains(world.browser)
    chain.move_to_element_with_offset(el, 20, 20)
    chain.click_and_hold(None)
    chain.move_by_offset(300, 100)
    chain.release(None)
    chain.perform()

@step(u'I click "([^"]*)" for document (\d+)')
def i_click_span_for_document_num(step, buttontext, docnum):
    doc = csss('.edit-document')[int(docnum) - 1]
    el = span_with_text(buttontext, doc)
    el.click()
    #hard_click(el)
    time.sleep(2) # give it time to process images.

@step(u'document (\d+) is (not )?saved and published')
def document_is_saved_and_published(step, docnum, notsaved):
    doc_el = csss('.edit-document')[int(docnum) - 1]
    doc_model = Document.objects.get(
        pk=int(doc_el.get_attribute("data-document-id"))
    )
    status = "unknown" if notsaved else "published"
    assert doc_model.status == status, "Expected %s; got %s" % (
            status, doc_model.status
    )

@step(u'I see a post with the title "([^"]*)"')
def i_see_a_post_with_the_title(step, title):
    for el in csss(".post-title-line h2"):
        if el.text == title:
            return
    assert "Post with title '%s' not found." % title

@step(u'I see an error')
def i_see_an_error(step):
    assert len(csss(".error")) > 0
