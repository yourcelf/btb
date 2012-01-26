import re
import time

from lettuce import *
from lettuce.django import django_url
from selenium.common.exceptions import NoSuchElementException
from selenium import webdriver

from django.contrib.auth.models import User, Group
from profiles.models import Organization

@before.all
def get_browser():
    world.browser = webdriver.Firefox()
    world.browser.implicitly_wait(1)

@before.all
def set_up_user():
    clear_test_users()
    add_test_users()

@after.all
def close_browser(*args, **kwargs):
    world.browser.close()
    clear_test_users()

def add_test_users():
    # Commenter
    u, created = User.objects.get_or_create(username="testuser")
    u.set_password("testuser")
    u.save()

    # Organization
    o, created = Organization.objects.get_or_create(
        name="testorg", slug="testorg"
    )

    # Moderator
    u, created = User.objects.get_or_create(username='testmod')
    u.groups.add(Group.objects.get(name='moderators'))
    u.set_password("testmod")
    u.save()
    o.moderators.add(u)

    # Author
    u, created = User.objects.get_or_create(username='testauthor')
    u.profile.display_name = "Test Author"
    u.profile.blogger = True
    u.profile.managed = True
    u.profile.consent_form_received = True
    u.profile.save()
    o.members.add(u)

def clear_test_users():
    try:
        User.objects.get(username="testuser").delete()
    except User.DoesNotExist:
        pass
    try:
        User.objects.get(username="testmod").delete()
    except User.DoesNotExist:
        pass
    try:
        User.objects.get(username="testauthor").delete()
    except User.DoesNotExist:
        pass
    try:
        Organization.objects.get(name="testorg").delete()
    except Organization.DoesNotExist:
        pass

@step(r'I access the url "(.*)"')
def access_url(step, url):
    world.browser.get(django_url(url))

@step(r'I follow "([^"]*)"')
def follow_url(step, text):
    link = world.browser.find_element_by_link_text(text)
    link.click()

@step(r'I follow the span (beginning )?"([^"]*)"')
def follow_the_span(step, beginning, text):
    """
    For non-anchor links (javascript span links)
    """
    els = world.browser.find_elements_by_tag_name("span")
    for el in els:
        if beginning: 
            if el.text.strip().startswith(text):
                return el.click()
        elif el.text.strip() == text:
            return el.click()

@step('I wait (\d+) seconds?')
def i_wait_for(step, seconds):
    time.sleep(float(seconds))

@step(r'I see the page contents "(.*)"')
def see_page_contents(step, text):
    page = world.browser.find_element_by_id("page")
    assert page.text.strip() == text

@step(r'I see the header "([^"]*)"')
def see_header(step, text):
    header = world.browser.find_element_by_tag_name("h1")
    assert header.text.strip() == text


@step(u'I am redirected to login')
def i_am_redirected_to_login(step):
    # URL is correct....
    assert world.browser.current_url.split("?")[0] == django_url("/accounts/login/"), "Expected %s, got %s" % (django_url("/accounts/login/"), world.browser.current_url.split("?")[0])
    # ... and login form exists (e.g. page rendered properly)
    world.browser.find_element_by_class_name('login-form')

@step('I am signed in( as a moderator for "([^"]*)")?')
def i_am_signed_in(step, moderator, org):
    access_url(step, "/accounts/login/?next=/")
    if not moderator:
        i_login_as(step, "testuser", "testuser")
    else:
        u = User.objects.filter(organizations_moderated__name=org)[0]
        # Assume username is password for test users.
        i_login_as(step, u.username, u.username)
    assert world.browser.current_url == django_url("/"), "Login failed."

@step('I login as "([^:]*):([^"]*)"')
def i_login_as(step, username, password):
    uname_el = world.browser.find_element_by_id("id_username")
    uname_el.send_keys(username)
    pword_el = world.browser.find_element_by_id("id_password")
    pword_el.send_keys(password)
    i_click_the_button(step, "Login")

@step(u'I click the button "([^"]*)"')
def i_click_the_button(step, value):
    el = world.browser.find_element_by_xpath('//input[@value="%s"]' % value)
    el.click()

@step(u'I click the submit button')
def i_click_the_submit_button(step):
    el = world.browser.find_element_by_xpath('//input[@type="submit"]')
    el.submit()

@step(u'I click the button named "([^"]*)"')
def i_click_the_button_named(step, value):
    el = world.browser.find_element_by_name(value)
    el.click()

@step(u'I (un)?check the "([^"]*)" checkbox')
def set_checkbox(step, un, name):
    box = world.browser.find_element_by_name(name)
    if un and box.get_attribute("checked") or \
            not un and not box.get_attribute("checked"):
        box.click()

@step(u'I get a 404')
def i_get_a_404(step):
    title = world.browser.find_element_by_tag_name('title')
    assert "404" in title.text, "Expected 404, but got something else: %s" % title.text
