unless window.btb?
  window.btb = {}
btb = window.btb

btb.strToDate = (dateOrStr) ->
    if _.isString dateOrStr
        parts = [parseInt(part, 10) for part in dateOrStr.split(/[^0-9]+/g)][0]
        # Months are rendered as 0-11 in javascript
        return new Date(
          parts[0],
          parts[1] - 1,
          parts[2],
          parts[3] or 0,
          parts[4] or 0,
          parts[5] or 0)
    return dateOrStr

btb.formatDate = (dateOrStr) ->
    d = btb.strToDate(dateOrStr)
    d.getFullYear() + "-" + (1 + d.getMonth()) + "-" + d.getDate()

btb.formatDateWithZeros = (dateOrStr) ->
    d = btb.strToDate(dateOrStr)
    month = (1 + d.getMonth())
    if month < 10 then month = "0#{month}"
    day = d.getDate()
    if day < 10 then day = "0#{day}"
    d.getFullYear() + "-" + month + "-" + d.getDate()

btb.formatDateTime = (dateOrStr) ->
    d = btb.strToDate()
    btb.formatDate(d) + " " + d.getHours() + ":" + d.getMinutes()

btb.dateInterval = (d1, d2) ->
    interval = Math.abs(
        btb.strToDate(d1).getTime() - btb.strToDate(d2).getTime()
    )
    return interval / 1000

btb.englishDateInterval = (d1, d2) ->
    interval = btb.dateInterval(d1, d2)
    if interval < 60
        i = parseInt(interval)
        word = "second"
    else if interval < 60 * 60
        i = parseInt(interval / 60)
        word = "minute"
    else if interval < 60 * 60 * 24
        i = parseInt(interval / 60 / 60)
        word = "hour"
    else
        i = parseInt(interval / 60 / 60 / 24)
        word = "day"
    return "#{i} #{word}" + (if i != 1 then "s" else "")

btb.ellipsisWithMore = (str, length=200) ->
    if str.length < length
        return str

    "<span>#{str.substr(0, 200)}</span>\n" +
    "<span style='display: none;'>#{str.substr(200)}</span>\n" +
    "<span class='link-like' onclick='$(this).prev().show(); $(this).hide();'>...</span>"


btb.zeroPad = (num, digits) ->
    num = "" + num
    while num.length < digits
        num = "0" + num
    num

# Cross-browser CSS3 linear-gradient.  Adapted from compass's +linear-gradient
# mixin; but settable via javascript.
btb.colorStripes = (selector, colors...) ->
    percent = 100.0 / (colors.length)
    standardStops = []
    oldWebkitStops = []
    for i in [0...colors.length]
        standardStops.push "#{colors[i]} #{percent * i}%, #{colors[i]} #{percent * (i + 1)}%"
        oldWebkitStops.push "color-stop(#{percent * i}%, #{colors[i]}), color-stop(#{percent * (i + 1)}%, #{colors[i]})"
    standardArgs = "top, " + standardStops.join(", ")
    oldWebkitArgs = "linear, 50% 0%, 50% 100%, " + oldWebkitStops.join(", ")
    $(selector).css("background-image", "-webkit-gradient(#{oldWebkitArgs})")
    compats = [
        "-webkit-linear-gradient", "-moz-linear-gradient"
         "-o-linear-gradient", "-ms-linear-gradient",
         "linear-gradient"
    ]
    for func in compats
         $(selector).css("background-image", "#{func}(#{standardArgs})")

# Cross-browser CSS3 transform.  Adapted from compass's +simple-transform
# mixin; but settable via javascript.
btb.transform = (selector, scale, rotate, translateXY, originXY) ->
    trans = "scale(#{scale}, #{scale}) rotate(#{rotate}) translate(#{translateXY[0]}, #{translateXY[1]})"
    origin = originXY.join(" ")
    for prefix in ["-moz-", "-webkit-", "-o-", "-ms-", ""]
        $(selector)
            .css("#{prefix}transform", trans)
            .css("#{prefix}transform-origin", origin)

class btb.FilteredPaginatedCollection extends Backbone.Collection
    pagination: {}
    filter: {}

    url: -> if @filter then "#{@baseUrl}?#{$.param(@filter)}" else @baseUrl

    parse: (response) ->
        @pagination = response.pagination
        response.results
    
    fetchById: (id, options) =>
        @filter = {id: id}
        @fetch options

class btb.PaginatedView extends Backbone.View
    paginationTemplate: _.template $("#pagination").html() or ""

    renderPagination: (collection, el) ->
        p = collection.pagination
        links = []
        for i in [1..(p.pages)]
            if i < 10 or Math.abs(p.page - i) < 5 or i > p.pages - 10
                links.push(i)

        el.html(@paginationTemplate({
            per_page: collection.filter?.per_page or 12
            pagination: p
            pageLinksToShow: links
            hideForSinglePage: @hideForSinglePage
        }))
        @$(".per-page").val(collection.filter?.per_page or 12)
        this

    newPageFromEvent: (event) -> parseInt $.trim $(event.currentTarget).text()
    setPageLoading: => $(".pagination-loading", @el).show()
    setPageDoneLoading: => $(".pagination-loading", @el).hide()

class btb.TabularList extends btb.PaginatedView
    tagName: 'table'
    events:
        'click span.pagelink': 'turnPage'
        'change select.per-page': 'setPerPage'

    initialize: (options) ->
        @collection = options.collection
        @columns = options.columns
    
    render: =>
        $(@el).html $("<tr/>").html(
            _.map(@columns, (c) -> "<th>#{ c.heading }</td>").join("")
        )
        @collection.each (obj) =>
            tr = $("<tr/>")
            for col in @columns
                tr.append $("<td/>").append(col.render obj)
            $(@el).append tr
        if @collection.length == 0
            $(@el).append $("<tr/>").append(
                $("<td/>").html("No results").attr("colspan", @columns.length)
            )
        else if @collection.pagination?
            pag = $("<td/>").attr { colspan: @columns.length }
            # Chrome bug setting class using attr with jQuery 1.6... 
            pag.addClass "pagination"
            $(@el).append $("<tr/>").html(pag)
            @renderPagination(@collection, pag)
        this

    turnPage: (event) =>
        @collection.filter.page = @newPageFromEvent event
        $(@el).addClass(".loading")
        @fetchItems()

    setPerPage: (event) =>
        event?.preventDefault()
        @collection.filter.per_page = parseInt(@$("select.per-page").val())
        @fetchItems()

    fetchItems: =>
        @setPageLoading()
        @collection.fetch
            success: =>
                @render()
                $(@el).removeClass(".loading")
            error: =>
                alert "Server error"
                $(@el).removeClass(".loading")

    # Default column types
    dateColumn: (name, heading="Date") ->
        heading: heading
        render: (obj) -> btb.formatDate(obj.get(name))

class btb.LiveCheckbox extends Backbone.View
    tagName: 'input'
    initialize: (options) ->
        @model = options.model
        @field = options.field

    events:
        'click': 'save'

    render: =>
        $(@el).attr
            type: "checkbox"
            checked: !!@model.get(@field)
            class: "editor"
        this

    save: =>
        attrs = {}
        attrs[@field] = $(@el).is(":checked")
        @model.set attrs
        @model.save {}, {
            success: (model, response) =>
                $(@el).parent().effect "highlight"
            error: =>
                $(@el).parent().addClass "ui-state-error"
                alert "Server error."
        }

class btb.EditInPlace extends Backbone.View
    tagName: 'span'
    template: _.template $("#editInPlace").html() or ""
    editorTemplate: _.template $("#editorInPlace").html() or ""
    events:
        'click span.cancel': 'render'
        'click span.edit-in-place': 'renderEditor'
        'click input.save': 'save'

    inputTypes:
        input: -> $("<input/>").attr("type", "text")
        textarea: -> $("<textarea/>")

    initialize: (options) ->
        @model = options.model
        @field = options.field
        @type = if options.type? then options.type else "input"
        @commitOnSave = true unless options.commitOnSave == false

    render: =>
        $(@el).html @template { field: @model.get(@field) }
        this

    renderEditor: =>
        span = $(".edit-in-place", @el)
        span.hide()
        span.after @editorTemplate
        input = @inputTypes[@type]()
        input.val @model.get(@field)
        input.addClass "editor"
        $(".edit-tag", @el).replaceWith input
        input.focus()
        this

    save: =>
        attrs = {}
        attrs[@field] = $(".editor", @el).val()
        @model.set attrs
        $(@el).addClass(".loading")
        if @commitOnSave
            @model.save {},
                success: (model, response) =>
                    $(@el).removeClass(".loading")
                    @model = model
                    $(@el).parent().effect "highlight"
                error: =>
                    $(@el).removeClass(".loading")
                    $(@el).parent().addClass "ui-state-error"
                    alert "Server error"
        @render()

btb.EditInPlace.factory = (modelsets) ->
    # Given a top-level selector, and an array of 
    #   [model, field, selector, type (optional)]
    #
    # transform all the selectors to edit-in-place controls.
    editors = []

    for [model, field, selector, type...] in modelsets
        attrs =
            model: model
            field: field
        if type.length > 0
            attrs.type = type[0]
        if attrs.type == "checkbox"
            editor = new btb.LiveCheckbox attrs
        else
            editor = new btb.EditInPlace attrs
        el = editor.render().el
        $(selector).html editor.render().el
        editors.push editor
    editors

btb.stickyPlace = (el) ->
  scroll = $(window).scrollTop()
  win_height = $(window).height()
  parent = el.offsetParent()
  py1 = parent.position().top
  py2 = py1 + parent.height()
  height = el.height()

  top = Math.max(
    py1,
    Math.min(py2 - height, scroll)
  ) - py1
  el.css({
    top: top + "px"
    maxHeight: win_height
  })
