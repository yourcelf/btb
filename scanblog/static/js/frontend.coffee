# CSRF protection for Django.
$('html').ajaxSend (event, xhr, settings) ->
    if not /^http:.*/.test(settings.url) || /^https:.*/.test(settings.url)
        # Only send the token to relative URLs i.e. locally
        xhr.setRequestHeader "X-CSRFToken", $.cookie('csrftoken')

do ->
  months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
  days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
  date = new Date()
  while date.getDay() != 1
      date = new Date(date.getTime() + (1000*60*60*24))
  $(".comment-maildate").html("#{days[date.getDay()]}, #{date.getDate()} #{months[date.getMonth()]} #{date.getFullYear()}")


$("a.hide, a.show", ".blog-nav-bar").on "click", ->
  links = $(".blog-nav-bar .links").slideToggle()
  $(".blog-nav-bar").toggleClass("open")
  return false
