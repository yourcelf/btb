from lettuce import *

from selenium.webdriver.common.action_chains import ActionChains

def css(selector, scope=None):
    """
    Return first element matching css selector.
    """
    scope = scope or world.browser
    return scope.find_element_by_css_selector(selector)

def csss(selector, scope=None):
    """
    Return all elements matching css selector.
    """
    scope = scope or world.browser
    return scope.find_elements_by_css_selector(selector)

def hard_click(el):
    """
    Sometimes selenium seems to be unable to properly click.  This is more
    reliable.
    """
    #href = el.get_attribute("href")
    #world.browser.get(href)
    chain = ActionChains(world.browser)
    chain.click_and_hold(el)
    chain.release(None)
    chain.perform()

def span_with_text(text, scope=None):
    for el in csss("span", scope):
        if el.text == text:
            return el
    assert 0, "Span with text '%s' not fond." % text

def eq_(a, b):
    assert a == b, "'%s' != '%s'" % (a, b)
