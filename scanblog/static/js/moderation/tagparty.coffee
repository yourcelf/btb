unless window.btb? then window.btb = {}

class btb.Tag extends Backbone.Model
class btb.TagList extends Backbone.Collection
  url: "/moderation/tagparty/tags/"
  model: btb.Tag

class btb.TagForm extends Backbone.View
  template: _.template $("#tagpanelTemplate").html() or ""
  events:
    "submit form.tagparty": "saveTags"
    "click a.tag": "addTag"
    "change form.tagparty select": "rechoose"

  initialize: (options) ->
    @possible = new btb.TagList()
    @possible.reset options.tags
    console.log @possible
    @chosen = []
    @fetchDocument()

  fetchDocument: =>
    $.ajax
      url: "/moderation/tagparty/next/"
      type: "get"
      success: (data) =>
        doc = $("<div>#{data}</div>")
        $("#doc").html doc.find(".post-detail").html()
        @chosen = ($.trim($(li).text()) for li in doc.find("ul.tags li"))
        @tagURL = doc.find(".tagform form").attr("action")
        @render()
      error: (xhr, statusText, error) =>
        switch xhr.status
          when 404 then alert "No more untagged posts!"
          else alert "Server error!"

  rechoose: =>
    @chosen = @$("select", "form.tagparty").val() or []
    @render()

  render: =>
    $("#tagpanel").html @el
    possible = []
    for tag in @possible.models
      unless _.contains @chosen, tag.get("name")
        possible.push name: tag.get("name"), chosen: false
    @$el.html @template
      possible: possible
      chosen: @chosen
    @$(".chosen-tags").tagit
      tagSource: _.map(possible, (a) -> a.name)
      triggerKeys: ['enter', 'comma', 'tab']
      allowNewTags: false
      select: true
    @delegateEvents()

  saveTags: (event) =>
    $(event.currentTarget).addClass("loading")
    tags = (@$("select", "form.tagparty").val() or []).join(",")
    $.ajax
        url: @tagURL
        success: =>
            $(event.currentTarget).removeClass("loading")
            @$(".status").addClass("success").html("All good!")
        error: =>
            alert "Server error"
            $(event.currentTarget).removeClass("loading")
            @$(".status").addClass("warn").html("Oh no!")
        type: "POST",
        data: { tags: tags }

    return false

  addTag: (event) =>
    @chosen.push $.trim $(event.currentTarget).text()
    @render()
    return false

