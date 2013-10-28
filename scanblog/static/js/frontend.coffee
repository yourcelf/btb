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


$(".blog-nav-bar a.toggle").on "click", ->
  if $(this).hasClass("open")
    openit = false
  else
    openit = true
  # close everything.
  $(".blog-nav-bar .toggle.open").removeClass("open")
  $(".blog-nav-bar .target.open").removeClass("open").show().slideToggle()
  if openit
    $($(this).attr("data-target"), ".blog-nav-bar").hide().slideToggle().addClass("open")
    $(this).addClass("open")
  return false

toggle_favorite = (event) ->
  event.preventDefault()
  $(event.currentTarget).addClass("loading")
  url = $(event.currentTarget).attr("href")
  params = url.split("?")[1]
  data = {}
  for arg in params.split("&")
    kv = arg.split("=")
    data[decodeURIComponent(kv[0])] = decodeURIComponent(kv[1])
  $.ajax {
    url: url
    type: 'POST'
    data: data
    success: (data) ->
      replacement = $(data)
      $(event.currentTarget).closest(".favorites-control").replaceWith(replacement)
      add_favorite_triggers(replacement.parent())
    error: ->
      alert("Server error")
  }

get_favorites = (event) ->
  event.preventDefault()
  el = $(event.currentTarget)
  popover = el.closest(".count").find(".favorites-popover")
  if popover.is(":visible")
    popover.hide()
  else
    popover.show()
    popover.find(".close").on("click", -> popover.hide())
    url = el.attr("href")
    $.ajax {
      url: url
      type: 'GET'
      success: (data) ->
        content = popover.find(".content")
        content.html(data)
        # Doing it this way because of bugs with chrome refreshing auto.
        if content.height() > 200
          content.css({
            "maxHeight": "200px",
            "overflow": "auto"
          })
      error: ->
        alert("Server error")
    }

add_favorite_triggers = (parent) ->
  $(".favorites-control a.toggle", parent).on "click", toggle_favorite
  $(".favorites-control a.get-favorites", parent).on "click", get_favorites
add_favorite_triggers(document)

# Clear popovers on click outside
$(document).mouseup (event) ->
  triggers = $(".popover-trigger")
  if triggers.is(event.target)
    return
  popovers = $(".popover")
  if popovers.has(event.target).length == 0
    popovers.hide()
