import time

from lettuce import *
from lettuce.django import django_url

from btblettuce import *
from scanning.models import PendingScan

@step(u'I see the incoming mail form')
def i_see_the_incoming_mail_form(step):
    css(".pending-scans")

@step(u'a pendingscan entry for that choice is created')
def a_pendingscan_entry_for_that_choice_is_created(step):
    time.sleep(1) # argh selenium
    qs = PendingScan.objects.filter(author__pk=world.chosen_user_pk)
    assert len(qs) > 0
    world.chosen_pending_scan = qs[0].pk

@step(u'I see that user choice in the pending list')
def i_see_that_user_choice_in_the_pending_list(step):
    time.sleep(1) # argh selenium
    for el in csss(".pending-scan-list .user-id"):
        if int(el.text) == world.chosen_user_pk:
            return
    assert 0, "User no found in pending scan list."

@step(u'I click the missing checkbox')
def i_click_the_missing_checkbox(step):
    # Re-fetch, because AJAX refresh sometimes borks selenium
    world.browser.get(django_url("/moderation/#/pending"))
    for i,el in enumerate(csss(".pending-scan-list tr.item")):
        id_input = el.find_element_by_css_selector("input.pending-scan-id")
        if int(id_input.get_attribute("value")) == world.chosen_pending_scan:
            el.find_element_by_css_selector(
                "input.pending-scan-missing"
            ).click()
            return
    assert 0, "Missing checkbox not found"

@step(u'the pendingscan entry is marked missing')
def the_pendingscan_entry_is_marked_missing(step):
    assert len(PendingScan.objects.missing().filter(pk=world.chosen_pending_scan)) == 1

@step(u'I see the choice under the missing list in the user detail page')
def i_see_the_choice_under_the_missing_list_in_the_user_detail_page(step):
    ps = PendingScan.objects.get(pk=world.chosen_pending_scan)
    world.browser.get(django_url("/moderation/#/users/%s" % ps.author.pk))
    for el in csss("input.pending-scan-missing"):
        if int(el.get_attribute("data-id")) == ps.pk:
            assert bool(el.get_attribute("checked"))
            return
    assert 0, "Missing scan entry not found in user detail page"

@step(u'I delete the first missing choice')
def i_delete_the_first_missing_choice(step):
    world.browser.get(django_url("/moderation/#/pending"))
    css(".show-missing").click()
    time.sleep(1) # argh selenium
    ps = PendingScan.objects.get(pk=world.chosen_pending_scan)
    for el in csss(".remove-pending-scan"):
        if int(el.find_element_by_css_selector(".pending-scan-id").get_attribute("value")) == ps.pk:
            el.find_element_by_css_selector(".link-like").click()
            break
    else:
        assert 0, "Trash link not found."
    assert len(PendingScan.objects.filter(pk=world.chosen_pending_scan)) == 0

@step(u'the choice disappears')
def the_choice_disappears(step):
    time.sleep(1) # argh selenium
    for el in csss(".remove-pending-scan"):
        if int(el.find_element_by_css_selector(".pending-scan-id").get_attribute("value")) == world.chosen_pending_scan:
            assert 0, "Pending scan didn't disappear when deleted."
