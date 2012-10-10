import re
import time

from lettuce import *
from lettuce.django import django_url
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium import webdriver

from django.contrib.auth.models import User
from comments.models import Comment
from btblettuce import *

@step(u'I see links to "([^"]*)" and "([^"]*)"')
def i_see_links_to(step, word1, word2):
    for word in [word1, word2]:
        el = world.browser.find_element_by_link_text(word)

@step(u'I see "([^"]*)" in the auth section')
def i_see_in_the_auth_section(step, word):
    el = css(".auth")
    assert word in el.text

@step(u'I see the login form')
def i_see_the_login_form(step):
    world.browser.find_elements_by_class_name("login-form")

@step(u'I see the registration form')
def i_see_the_registration_form(step):
    world.browser.find_elements_by_class_name("register-form")

@step(u'I am redirected to "([^"]*)"')
def i_am_redirected_to(step, url):
    assert world.browser.current_url == django_url(url), \
            "Expected %s, got %s" % (django_url(url), world.browser.current_url)

@step(u'the following registrations (don\'t )?work')
def then_the_following_registrations_work(step, dont):
    for obj in step.hashes:
        if obj['delete'] == 'yes':
            try:
                User.objects.get(username=obj['username']).delete()
            except User.DoesNotExist:
                pass
        url = django_url("/accounts/register/")
        world.browser.get(url)
        for name in ("username", "email", "password1", "password2"):
            el = world.browser.find_element_by_name(name)
            el.clear()
            el.send_keys(obj[name])
        el.submit()
        if dont:
            world.browser.find_element_by_class_name("errorlist")
            assert world.browser.current_url.split("?")[0] == url
        else:
            i_see_in_the_auth_section(step, obj["username"])
            assert world.browser.current_url == django_url("/accounts/welcome/")
            try:
                u = User.objects.get(username=obj['username'])
            except User.DoesNotExist:
                assert 0, "User registration failed for %s" % obj['username']
            if obj['delete'] == 'yes':
                u.delete()


@step('I am a user named "([^"]*)" with comments')
def i_am_a_user_with_comments(step, uname):
    try:
        User.objects.get(username=uname).delete()
    except User.DoesNotExist:
        pass
    world.browser.get(django_url("/accounts/register/"))
    for name in ("username", "password1", "password2"):
        el = world.browser.find_element_by_name(name)
        el.send_keys(uname)
        time.sleep(0.1)
    el.submit()
    world.working_user_pk = User.objects.get(username=uname).pk
    world.browser.get(django_url("/posts/5"))
    comment_entry = world.browser.find_element_by_name("comment")
    comment_entry.send_keys("My comment")
    comment_entry.submit()
    assert len(Comment.objects.filter(user__username=uname)) > 0

@step('I delete my account( and comments)?')
def i_delete_my_account(step, comments_too):
    world.browser.get(django_url("/"))
    #chain = ActionChains(world.browser)
    #chain.move_to_element(css(".auth .menu-trigger"))
    #chain.perform()
    hard_click(css(".auth .menu-trigger"))
    hard_click(world.browser.find_element_by_link_text("Profile"))
    hard_click(world.browser.find_element_by_link_text("Edit settings"))
    hard_click(world.browser.find_element_by_link_text("Delete account"))
    if comments_too:
        world.browser.find_element_by_name("delete_comments").click()
    world.browser.find_element_by_xpath('//input[@type="submit"]').submit()
    assert "successfully deleted" in css(".message").text

@step('the account "([^"]*)" is made inactive')
def account_is_inactive(step, username):
    assert User.objects.get(pk=world.working_user_pk).is_active == False

@step('the comments by "([^"]*)" are deleted')
def the_comments_are_deleted(step, uname):
    assert len(Comment.objects.filter(user__pk=world.working_user_pk)) == 0

@step('the comments by "([^"]*)" remain')
def the_comments_are_deleted(step, uname):
    assert len(Comment.objects.filter(user__pk=world.working_user_pk)) > 0

@step('the display name for "([^"]*)" is "([^"]*)"')
def the_comment_author_reads(step, username, display_name):
    assert User.objects.get(
            pk=world.working_user_pk
        ).profile.display_name == display_name
    world.browser.get(django_url("/posts/5/"))
    for el in world.browser.find_elements_by_css_selector(".commentbyline td"):
        if el.text.strip() == display_name:
            return
    assert 0, "Comment wasn't found."
    
@step('delete the working user')
def delete_the_working_user(step):
    try:
        User.objects.get(pk=world.working_user_pk).delete()
    except User.DoesNotExist:
        pass
