#
# Models and collections
#
class btb.Scan extends Backbone.Model
    url: -> btb.ScanList.prototype.baseUrl + "/" + @id
    parse: (response) ->
        response.results[0]

class btb.ScanList extends btb.FilteredPaginatedCollection
    model: btb.Scan
    baseUrl: "/scanning/scans.json"

class btb.ScanSplit extends Backbone.Model
    url: -> "/scanning/scansplits.json/" + @get("scan").id

#
# List view
#

class btb.ProcessingManager extends Backbone.View
    template: _.template $("#processManager").html()
    initialize: ->
        @scanView = new btb.ProcessScanListView()
        @docView = new btb.ProcessDocListView()
    
    render: =>
        $(@el).html(@template())
        $(".process-scan-list", @el).html @scanView.render().el
        $(".process-document-list", @el).html @docView.render().el
        this

class btb.ProcessItemListView extends btb.PaginatedView
    itemTemplate: _.template($("#processItem").html())
    events:
        "click span.pagelink": "turnPage"

    defaultFilter: {}

    initialize: (options=listClass: btb.DocumentList)->
        @list = new options.listClass()
        @list.filter = _.extend({}, @defaultFilter)

    fetch: =>
        @startLoading()
        @list.fetch
            success: =>
                @stopLoading()
                @renderDetails()
            error: =>
                @stopLoading()
                alert "Server error"

    startLoading: =>
        $(@el).addClass("loading")

    stopLoading: =>
        $(@el).removeClass("loading")

    render: ->
        $(@el).html "<ul class='process-list'></ul><div class='pagination'></div>"
        @fetch()
        this

    renderDetails: ->
        html = ''
        if @list.models.length == 0
            $('ul', @el).html("<li>None found.</li>")
        else
            for obj in @list.models
                html += @itemTemplate obj: obj.toJSON()
            $('ul', @el).html(html)
        @renderPagination @list, $(".pagination", @el)
    
    turnPage: (event) =>
        page = @newPageFromEvent(event)
        @list.filter.page = page
        @fetch()

class btb.ProcessDocListView extends btb.ProcessItemListView
    defaultFilter:
        page: 1
        per_page: 6
        status: "unknown"

    initialize: ->
        super listClass: btb.DocumentList

    renderDetails: =>
        super()
        $(".delete-scan", @el).remove()
        this

class btb.ProcessScanListView extends btb.ProcessItemListView
    defaultFilter:
        page: 1
        per_page: 6
        processing_complete: 0

    initialize: ->
        super listClass: btb.ScanList


#############################################################################
# Scan splitter view
#
class btb.SplitScanView extends Backbone.View
    template: _.template $("#splitScan").html()
    lockTemplate: _.template $("#splitScanEditLockWarning").html()

    minimumTypes: ["post", "profile", "photo", "request", "license"]
    addableTypes: ["post", "profile", "photo", "request"]

    typeColors:
        "post": ["#0f0", "#00f", "#0a0", "#00a"]
        "profile": ["#0ff"]
        "photo": ["#f0f", "#a0a", "#606"]
        "request": ["#f00"]
        "license": ["#ff0"]
        "ignore": ["#000"]

    events:
        'click .switch-to-edit-documents': 'switchToDocumentView'
        'mouseover div.page-image': 'mouseOverPage'
        'click .next': 'nextPage'
        'click .prev': 'prevPage'
        'click .pagestatus': 'jumpToPage'
        'click .add-post': 'addPostChoice'
        'click .add-photo': 'addPhotoChoice'
        'click .save': 'save'
        'click .page-size-chooser span': 'setPageSize'
        'keyup .choose-code input': 'chooseCode'

    initialize: (scanId) ->
        @split = new btb.ScanSplit {scan: id: parseInt(scanId)}
        @split.fetch
            success: @initSplit
        $(window).keyup @keyUp
        @imgScale = 1
        this

    initSplit: (model) =>
        @loadSplit(model)
        @render()
        @setDirty(false)
        @checkFinished()
        @selectPage(0)

    keyUp: (event) =>
        # Don't capture events if we're in an input.
        if $("input:focus, textarea:focus").length > 0
            return
        switch event.keyCode
            when 32,78,39  then @nextPage(event) # spacebar, n, right
            when 8,80,37 then @prevPage(event) # backspace, p, left
            when 61,187 then @addPostChoice(event) # equals/plus
            when 220 then @addPhotoChoice(event) # back slash
            #when 13        then @save(event) # enter
            when 73, 192 then @ignoreView._toggleChoice(event) # i, backtick
            else
                if 48 <= event.keyCode <= 57 # 0 to 9
                    index = (event.keyCode - 48) - 1
                    if index == -1
                        index = 9
                    if index < @choiceViews.length
                        @choiceViews[index]._toggleChoice(event)

    loadSplit: (split) =>
        @split = split
        @choices = []
        @typeCount = {}
        for doc in @split.get("documents")
            @addChoice(new btb.Document doc)
        for type in @minimumTypes
            if not @typeCount[type]?
                @addChoice(new btb.Document type: type)
        
        # Add "ignored" choices if we have them.
        @ignoreChoice = new btb.Document pages: [], choiceTitle: "ignore"
        if @split.get("scan").processing_complete
            @ignoreChoice.set(pages: @getUnassignedIds())

    save: (event) =>
        if $(".save", @el).hasClass("disabled")
            $(".post-save-message", @el).html("Not savable yet.").removeClass("success").removeClass("warn")
            setTimeout(
                => $(".post-save-message", @el).html(""),
                2000)
            return
        @checkFinished()
        @split.set("documents": @choices)
        $(".save", @el).addClass("loading")
        @split.save {},
            success: (model) =>
                $(".save", @el).removeClass("loading")
                @initSplit(model)
                if @split.get("scan").processing_complete
                    $(".post-save-message", @el).html("&check; All good.").addClass("success")
                else
                    $(".post-save-message", @el).html("Saved, but still needs attention").addClass("warn")
            error: (model, error) =>
                alert("Server error")
                $(".save", @el).removeClass("loading")

    getAssignedIds: =>
        return _.union(
            @ignoreChoice.get("pages"),
            (c.get("pages") for c in @choices when c.get("pages")?)...
        )

    getUnassignedIds: =>
        pageIds = []
        for p in @split.get("scan").pages
            pageIds.push p.id
        assignedIds = @getAssignedIds()
        return _.difference(pageIds, assignedIds)

    addChoice: (doc) =>
        type = doc.get "type"
        @typeCount[type] = (@typeCount[type] or 0) + 1
        title = type
        if @typeCount[type] > 1
            title += " "  + @typeCount[type]
        doc.set choiceTitle: title
        @choices.push doc

    userAddChoice: (type) =>
        doc = new btb.Document type: type
        if @currentPageIndex?
            doc.set "pages": [@split.get("scan").pages[@currentPageIndex].id]
        @addChoice(doc)
        @render()
        @checkFinished()
        if @currentPageIndex?
            @selectPage(@currentPageIndex)

    addPostChoice: (event) => @userAddChoice("post")
    addPhotoChoice: (event) => @userAddChoice("photo")

    removeChoice: (type) =>
        alert("TODO")

    mouseOverPage: (event) =>
        i = parseInt($("input[name=page-index]", event.currentTarget).val())
        @selectPage(i)

    selectPage: (pageIndex) =>
        @currentPageIndex = pageIndex
        $(".in-viewport", @el).removeClass("in-viewport")
        $(".page-#{pageIndex}", @el).addClass("in-viewport")
        pages = @split.get("scan").pages
        $(".current-page", @el).html "Page #{pageIndex+1}/#{pages.length}"
        view.setDisplay(pages[pageIndex].id) for view in @choiceViews
        @ignoreView.setDisplay(pages[pageIndex].id)

    updateType: (doc, value) =>
        @setDirty(true)
        if @currentPageIndex?
            id = @split.get("scan").pages[@currentPageIndex].id
            pages = doc.get("pages") or []
            if value and id not in pages
                pages.push id
            else if not value
                pages = _.select pages, (n) -> n != id
            doc.set { pages }
            @checkFinished()

    setDirty: (val) =>
        @dirty = val
        saveEnabled = @dirty and @split.get("scan").author?.id?
        $(".save", @el).toggleClass("disabled", !saveEnabled)
        $(".switch-to-edit-documents", @el).toggleClass("disabled",
            (
                @dirty or
                not @split.get("scan").processing_complete or
                @getEditableDocuments().length == 0
            )
        )

    checkFinished: =>
        # Update the UI to reflect page statuses, and return 
        # bool(every page is assigned)
        
        assigned = @getAssignedIds()
        # Clear old page status UI
        $(".pagestatus").removeClass("assigned")
        $(".pagestatus .overlay").css("background-image", "none")
        for id in assigned
            $("#status#{id}").addClass("assigned")

        # Get the colors for each page
        colors = {}
        typeMod = {}
        for choice in @choices
            type = choice.get("type")
            typeMod[type] = if typeMod[type]? then typeMod[type] + 1 else 0
            for id in choice.get("pages") or []
                if not colors[id]?
                    colors[id] = []
                color = @typeColors[type][typeMod[type] % @typeColors[type].length]
                colors[id].push color
        for id in @ignoreChoice.get("pages") or []
            colors[id] = [@typeColors.ignore[0]]

        # Set the colors for each page
        for id in assigned
            btb.colorStripes("#status#{id} .overlay", colors[id]...)

        # Return complete status
        finished = @getUnassignedIds().length == 0 and @split.get("scan").author?.id?
        @split.get("scan").processing_complete = finished
        return finished

    render: =>
        scan = @split.get "scan"
        if scan.pages?
            $(@el).html @template { scan }
            #
            # Add the user switcher.
            #
            if scan.author
                user = new btb.User scan.author
            else
                user = null
            @userToggle = new btb.InPlaceUserChooser(user)
            @userToggle.bind "chosen", (user) =>
                @chooseUser(user)
                @setDirty(true)
            $(".user-chooser-holder", @el).html @userToggle.render().el
            # Replace the usual placeholder text with author-specific
            $(".user-chooser-trigger", @el).attr "placeholder", "Author"

            #
            # Add the ignore control.
            #
            @ignoreView = new btb.SplitScanPageDocChoice choice: @ignoreChoice
            @ignoreView.bind "toggleChoice", (choice, value) =>
                @updateType(choice, value)
                @setIgnore(value)
            $(".ignore-choice", @el).append(@ignoreView.render().el)
            
            # 
            # Add the type choice controls.
            #
            @choiceViews = []
            for choice in @choices
                choiceView = new btb.SplitScanPageDocChoice choice: choice
                choiceView.bind "toggleChoice", (choice, value) =>
                    @updateType(choice, value)
                    if value
                        @updateType(@ignoreChoice, false)
                        @setIgnore(false)
                $(".type-list", @el).append(choiceView.render().el)
                @choiceViews.push choiceView
            @buildScroller()

            #
            # Add notes
            #
            $(".note-manager", @el).append(
                new btb.NoteManager({
                    filter: {scan_id: scan.id}
                    defaults: {scan_id: scan.id}
                }).el
            )

        #
        # Lock warning
        #
        if @split.get("lock")?
            lock = @split.get("lock")
            $(".lock-warning", @el).append(@lockTemplate {
                name: lock.user.display_name
                created: lock.created
                now: lock.now
            })
        $(".page-image img").load =>
            @setPageScale parseFloat $.cookie("scanpagesize") or 1
        this

    chooseCode: (event) =>
        code = $(event.currentTarget).val()
        @split.get("scan").pendingscan_code = ""
        @setDirty(true)
        if !$.trim(code)
            $(".choose-code input", @el).removeClass("error")
            return
        else
            $(event.currentTarget).addClass "loading"
            $.get "/scanning/scancodes.json", term: code, (data) =>
                $(event.currentTarget).removeClass "loading"
                for ps in data
                    if ps.code == code
                        $(".choose-code input", @el).removeClass("error")
                        @userToggle.setUser new btb.User ps.author
                        @split.get("scan").pendingscan_code = code
                        return
        $(".choose-code input", @el).addClass("error")

    buildScroller: () =>
        n = @split.get("scan").pages.length
        width = $(".page-scroller", @el).width()
        height = $(".page-scroller", @el).height()
        aspect = 11 / 8.5 # constrained aspect for every page

        # Search for the number of rows that wastes the least space -- first by
        # maximizing width, and then by maximizing height.
        best = {}
        wastedSpace = 100000000000 # arbitrarily high
        for numRows in [1..n]
            perRow = Math.ceil n / numRows
            pageHeight = Math.min height, Math.floor(height / numRows)
            pageWidth = Math.floor(pageHeight / aspect)
            if pageHeight * numRows > height or pageWidth * perRow > width
                continue
            waste = height * width - (pageHeight * pageWidth * n)
            if waste < wastedSpace
                wastedSpace = waste
                best =
                    strategy: "row"
                    numRows: numRows
                    numCols: perRow
                    pageHeight: pageHeight
                    pageWidth: pageWidth
        for numCols in [1..n]
            perCol = Math.ceil n / numCols
            pageWidth = Math.min width, Math.floor(width / numCols)
            pageHeight = Math.floor pageWidth * aspect
            if (pageWidth * numCols) > width or (pageHeight * perCol) > height
                continue
            waste = height * width - (pageHeight * pageWidth * n)
            if waste < wastedSpace
                wastedSpace = waste
                best =
                    strategy: "col"
                    numRows: perCol
                    numCols: numCols
                    pageHeight: pageHeight
                    pageWidth: pageWidth
        $(".pagestatus", @el).width(best.pageWidth - 2) # Leave 2px for border
        $(".pagestatus", @el).height(best.pageHeight - 2)
        $(".page-scroller", @el).height(best.pageHeight * best.numRows)

    setIgnore: (value) =>
        if value
            for view in @choiceViews
                @updateType(view.choice, false)
                view.toggleChoice(false, true) for view in @choiceViews
        else
            @ignoreView.toggleChoice(false, true)
            

    chooseUser: (user) =>
        @split.get("scan").author = user.toJSON()

    prevPage: (event) =>
        @scrollTo((@currentPageIndex or 0) - 1)

    nextPage: (event) =>
        @scrollTo((@currentPageIndex or 0) + 1)

    jumpToPage: (event) =>
        classes = event.currentTarget.className.split(/\s+/)
        for name in classes
            match = /page-(\d+)/.exec name
            if match
                index = parseInt match[1]
                @scrollTo index
                return

    scrollTo: (pageIndex) =>
        if 0 <= pageIndex < @split.get("scan").pages.length
            target = $(".page-image.page-#{pageIndex}", @el)
            $('html,body').animate({
                scrollTop: target.offset().top
            }, 200)
            @selectPage(pageIndex)

    pageSizes:
        small: 0.2
        medium: 0.5
        large: 1.0

    setPageSize: (event) =>
        $(event.currentTarget).removeClass("chosen")
        newScale = @pageSizes[event.currentTarget.className]
        @setPageScale(newScale)

    setPageScale: (newScale) =>
        $(".page-size-chooser span", @el).removeClass("chosen")
        for name, scale of @pageSizes
            if scale == newScale
                $(".page-size-chooser .#{name}", @el).addClass("chosen")
        for page in @split.get("scan").pages
            w = Math.min(page.image_dims[0], 900)
            h = w / page.image_dims[0] * page.image_dims[1]
            el = $(".page-image.page-#{page.order}", @el).width(
                w * newScale
            ).height(
                h * newScale
            )
            el.find("img").css(width: "100%", height: "100%")
        @imgScale = newScale
        $.cookie("scanpagesize", newScale)

    getEditableDocuments: =>
        return _.select @choices, (c) => c.get("pages")?.length > 0

    switchToDocumentView: =>
        if $(".switch-to-edit-documents", @el).hasClass("disabled")
            return
        editableIds = _.pluck @getEditableDocuments(), "id"
        btb.app.navigate("#/process/document/#{ editableIds.join(".") }", true)

class btb.SplitScanPageDocChoice extends Backbone.View
    tagName: "li"
    template: _.template $("#splitScanPageDocChoice").html()
    events:
        'click': '_toggleChoice'

    initialize: ({choice, chosen}) ->
        @choice = choice
        @chosen = chosen or false

    render: =>
        $(@el).html @template { title: @choice.get("choiceTitle"), chosen: @chosen }
        this

    _toggleChoice: (event) =>
        @toggleChoice(null, null)

    toggleChoice: (value, silent) =>
        @chosen = if value? then value else (not @chosen)
        @render()
        if not silent
            @trigger "toggleChoice", @choice, @chosen

    setDisplay: (pageId) =>
        @chosen = pageId in @chosenIds()
        @render()

    chosenIds: => @choice.get("pages") or []

