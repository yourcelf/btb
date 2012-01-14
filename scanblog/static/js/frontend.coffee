# CSRF protection for Django.
$('html').ajaxSend (event, xhr, settings) ->
    if not /^http:.*/.test(settings.url) || /^https:.*/.test(settings.url)
        # Only send the token to relative URLs i.e. locally
        xhr.setRequestHeader "X-CSRFToken", $.cookie('csrftoken')
