import time
from lettuce import *
from lettuce.django import django_url
from django.contrib.auth.models import User

from btblettuce import *

@step('I type "([^"]*)" in the user search form')
def i_type_text_in_the_user_search_form(step, text):
    el = css(".user-chooser-trigger")
    time.sleep(0.5)
    el.send_keys(text[0])
    time.sleep(0.5)
    el = css(".user-search")
    el.send_keys(text[1:])

@step('I see choices for users')
def i_see_choices_for_users(step):
    css(".user-chooser .results .compact-user")

@step('I click the first user choice')
def i_click_the_first_user_choice(step):
    el = css(".user-chooser .results .result")
    world.chosen_user_pk = int(el.find_element_by_css_selector(".user-id").text)
    el.click()

@step('I search for the user "([^"]*)"')
def i_search_for_the_user(step, text):
    world.browser.get(django_url("/moderation/#/users"))
    i_type_text_in_the_user_search_form(step, text)

@step('I see "([^"]*)" in the user list')
def i_see_text_in_the_user_list(step, text):
    list_text = css(".user-chooser-holder .results .noresult").text
    assert text in list_text, "'%s' not found in '%s'." % (text, list_text)

@step('I click the create user link')
def i_click_the_create_user_link(step):
    css(".user-chooser-holder .add-user-link").click()

@step('I see the create user form')
def i_see_the_create_user_form(step):
    return css(".user-chooser-holder form.add-user")

@step('the name field contains "([^"]*)"')
def the_name_field_contains_text(step, text):
    eq_(
        css(".user-chooser-holder input[name=display_name]").get_attribute("value"),
        text
    )

@step('I enter an address in the create user form')
def i_enter_an_address_in_the_create_user_form(step):
    textarea = css(".user-chooser-holder textarea[name=mailing_address]")
    textarea.send_keys("77 Amherst St\nCambridge, MA")

@step('a new user named "([^"]*)" is created')
def a_new_user_named_name_is_created(step, name):
    time.sleep(1)
    i_search_for_the_user(step, name)
    time.sleep(1)
    els = csss(".user-chooser-holder .results .display-name")
    for el in els:
        if el.text == name:
            return
    assert False, "User '%s' not found." % name

@step('there is no user named "([^"]*)"')
def there_is_no_user_named_name(step, name):
    try:
        delete_the_user(step, name)
    except User.DoesNotExist:
        pass

@step('delete the user "([^"]*)"')
def delete_the_user(step, name):
    u = User.objects.get(profile__display_name=name)
    u.delete()
