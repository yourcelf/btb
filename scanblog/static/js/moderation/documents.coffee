class btb.Document extends Backbone.Model
    url: -> btb.DocumentList.prototype.baseUrl + "/" + @id

class btb.DocumentList extends btb.FilteredPaginatedCollection
    model: btb.Document
    baseUrl: "/scanning/documents.json"

#############################################################################
# Document editor view
#

#
# View for many documents, in series.
#

class btb.EditDocumentManager extends Backbone.View
    template: _.template $("#editDocumentsManager").html()

    initialize: (options=documents: []) ->
        @documents = new btb.DocumentList
        @documents.filter.idlist = options.documents.join(".")
        @documents.fetch
            success: @render

    render: =>
        if @documents.length > 0
            $(@el).html @template( numdocs: @documents.length )
            i = 0
            for doc in @documents.models
                docview = new btb.EditDocumentView
                    doc: doc
                    num: @documents.length
                    order: i
                i++
                $(".document-list", @el).append docview.render().el
        this

#
# View for a single document, with many pages.
#
class btb.EditDocumentView extends Backbone.View
    template: _.template $("#editDocument").html()
    inReplyToTemplate: _.template $("#editDocumentInReplyTo").html()
    inReplyToCampaignTemplate: _.template $("#editDocumentInReplyToCampaign").html()
    pageSizes:
        small: 0.3
        medium: 0.6
        full: 1
    events:
        'click .small': 'pageSizeSmall'
        'click .medium': 'pageSizeMedium'
        'click .full': 'pageSizeFull'
        'click .save-doc': 'save'
        'keyup .doc-in-reply-to': 'checkInReplyToCode'

    initialize: (options=doc: null, num: 1, order: 0) ->
        @doc = options.doc
        @num = options.num
        @order = options.order

    render: =>
        $(@el).html @template(doc: @doc.toJSON(), num: @num, order: @order)
        @pageViews = []
        for page in _.sortBy(@doc.get("pages"), (p) -> p.order)
            do (page) =>
                pv = new btb.EditDocumentPageView
                    page: page
                    pagecount: @doc.get("pages").length
                # extract highlight
                ht = @doc.get("highlight_transform")
                if page.id == ht?.document_page_id
                    pv.setHighlightRelativeToCrop(ht.crop)
                pv.bind "highlightChanged", (crop) =>
                    if crop
                        ht =
                            crop: crop
                            document_page_id: pv.page.id
                        @doc.set("highlight_transform": ht)
                    else
                        @doc.set("highlight_transform": null)
                    for view in @pageViews
                        if view != pv
                            view.clearHighlight()
                pv.bind "movePageUp", => @swapPages(page.order - 1, page.order)
                pv.bind "movePageDown", => @swapPages(page.order, page.order + 1)
                pv.bind "cropping", (cropping) =>
                    for view in @pageViews
                        if view != pv
                            view.setCropping(cropping, false)

                pv.bind "highlighting", (highlighting) =>
                    for view in @pageViews
                        if view != pv
                            view.setHighlighting(highlighting, false)
                   
                @pageViews.push pv
                $(".page-list", @el).append(pv.render().el)

        userChooser = new btb.InPlaceUserChooser new btb.User(@doc.get "author")
        userChooser.bind "chosen", (model) =>
            @doc.set author: model.toJSON()
        $(".choose-user-holder", @el).append userChooser.render().el
        $(".doc-title", @el).change =>
            @doc.set title: $(".doc-title", @el).val()
        $(".doc-date", @el).change =>
            @doc.set date_written: $(".doc-date", @el).val()
        $(".doc-status", @el).val(@doc.get("status")).change =>
            @doc.set status: $(".doc-status", @el).val()
        $(".doc-adult", @el).change =>
            @doc.set adult: $(".doc-adult", @el).is(":checked")
        changeTags = =>
            @doc.set tags: $(".doc-tags", @el).val()
        $(".doc-tags", @el).smartTextBox({
            submitKeys: [13, 188]
            updateOriginal: true
            debug: true
            onElementAdd: changeTags
            onElementRemove: changeTags
        })
        $(".doc-in-reply-to", @el).change =>
            @doc.set in_reply_to: $(".doc-in-reply-to", @el).val()
        $(".document-notes-manager", @el).html(
            new btb.NoteManager({
                filter: {document_id: @doc.id}
                defaults: {document_id: @doc.id}
            }).el
        )
        $(".user-notes-table", @el).html(
            new btb.NoteViewTable({
                filter: {user_id: @doc.get("author").id, important: 1}
            }).render().el
        )
        @setPageSize()
        switch @doc.get("type")
            when "request"
                $(".correspondence-list", @el).html(
                    new btb.CorrespondenceManager({
                        recipient: new btb.User(@doc.get("author"))
                    }).el
                )
            when "license"
                $(".user-status-table", @el).html(
                    new btb.UserStatusTable(user: new btb.User(@doc.get("author"))).render().el
                )
        if @doc.get("in_reply_to")
            @checkInReplyToCode()
        this

    save: =>
        # validate
        errors = []
        $(".post-save-message", @el).html("")
        if @doc.get("type") == "post" and not @doc.get("highlight_transform")?.crop?.length > 0
            errors.push("Please add a highlighted section to a page.")

        d = new Date(@doc.get("date_written"))
        if isNaN d.getTime()
            errors.push("Please enter a valid date, in YYYY-MM-DD format.")
            $(".doc-date", @el).addClass("error")
        else
            $(".doc-date", @el).removeClass("error")
        if not @doc.get("author")
            errors.push("Please choose an author.")
            $(".choose-user-holder", @el).addClass("error")
        else
            $(".choose-user-holder", @el).removeClass("error")

        for error in errors
            $(".post-save-message", @el).append("<div class='error'>#{error}</div>")
        if errors.length == 0
            $(".save-doc", @el).addClass("loading")
            @doc.save {},
                success: =>
                    $(".save-doc", @el).removeClass("loading")
                    # Need to re-render, as @doc becomes disconnected from
                    # pages after saving.
                    @render()

                    type = @doc.get("type")
                    status = @doc.get("status")
                    if status == "unknown"
                        klass = "warn"
                        msg = "Document saved, but still needs attention.  Add a note explaining why?"
                    else if status == "published"
                        klass = "success"
                        msg = "&check; Document saved and published."
                        if not @doc.get("is_public")
                            klass = "warn"
                            msg = "Document saved and marked published, but author is not active or enrolled.
                                   The document will be published when the author is made active and enrolled."
                        if @doc.get("type") == "post" and not @doc.get("title")
                            msg += " Title left blank."
                    else if status == "unpublishable"
                        klass = "success"
                        msg = "Document saved, and marked unpublishable."
                    else if status == "ready"
                        klass = "success"
                        msg = "Document queued; will be published within 3 days."
                        if @doc.get("type") == "post" and not @doc.get("title")
                            msg += " Title left blank."
                    $(".post-save-message", @el).addClass(klass).html(msg)
                error: (model, response) =>
                    msg = "Server error - not saved. "
                    if response?.responseText?
                        msg += _.escapeHTML(response.responseText)
                        msg += " (code #{response.status})"
                    $(".save-doc", @el).removeClass("loading")
                    $(".post-save-message", @el).addClass("error").html(msg)

    swapPages: (from, to) =>
        frompage = _.select @pageViews, (pv) -> pv.page.order == from
        topage = _.select @pageViews, (pv) -> pv.page.order == to
        if not (frompage.length == 1 and topage.length == 1)
            return
        pages = [frompage[0], topage[0]]
        p2 = topage[0]
        [pages[0].page.order, pages[1].page.order] = [pages[1].page.order, pages[0].page.order]
        
        # Now comes the animated glory.

        # Pop the elements from teh dom, but add placeholder.
        holders = []
        offsets = ($(p.el).offset().top for p in pages)
        for i in [0...pages.length]
            offset = offsets[i]
            page = pages[i]
            el = $(page.el)
            holder = $("<div/>").attr(
                "class", "swap-placeholder"
            ).width(el.width()).height(el.height()).css({
                "background-color": "#eee"
                "z-index": 1
            })
            el.after(holder).css({
                position: 'absolute'
                top: offset.top
                left: offset.left
                zIndex: 1000
                opacity: 0.8
            })
            holders.push(holder)
        
        # Animate teh swap
        page = pages[0]
        dest = holders[1]
        for [page, dest] in [[pages[0], holders[1]], [pages[1], holders[0]]]
            do (page, dest) =>
                $(page.el).animate({
                    top: dest.position().top
                    left: dest.position().left
                }, 'slow', 'swing', =>
                    $(page.el).css({
                        position: 'static'
                        top: 'auto'
                        left: 'auto'
                        zIndex: 'auto'
                        opacity: 1
                    }).insertAfter(dest)
                    dest.remove()
                    page.render()
                )
    pageSizeSmall: (event) => @setPageSize(@pageSizes.small, event)
    pageSizeMedium: (event) => @setPageSize(@pageSizes.medium, event)
    pageSizeFull: (event) => @setPageSize(@pageSizes.full, event)
    setPageSize: (size, event) =>
        if size
            $.cookie("pagesize", size)
        else
            size = parseFloat $.cookie("pagesize") or 1
        $(".page-size span", @el).removeClass("active")
        for name, val of @pageSizes
            if val == size
                $("." + name, @el).addClass("active")
        for pv in @pageViews
            pv.scale = size
            pv.render()

    checkInReplyToCode: (event) =>
        input = $(".doc-in-reply-to", @el)
        details = $(".doc-in-reply-to-details", @el)
        val = input.val()
        details.html("")
        if val == ""
            input.removeClass("error")
            input.removeClass("loading")
            return

        input.addClass("loading")
        update = =>
            $.ajax
                url: "/annotations/reply_codes.json"
                type: "GET"
                data:
                    code: val
                    document: 1
                success: (data) =>
                    input.removeClass("loading")
                    if data.pagination.count != 1
                        input.addClass("error")
                    else
                        result = data.results[0]
                        console.log result
                        input.removeClass("loading")
                        if (result.document and
                              @doc.get("author").id != result.document.author.id)
                            error = "Warning: document author doesn't match" +
                                    " reply author -- wrong reply code?"
                        else
                            input.removeClass("error")
                            error = null
                        result.error = error
                        if result.document?
                            details.html(
                                @inReplyToTemplate(result)
                            )
                        else if result.campaign?
                            details.html(
                                @inReplyToCampaignTemplate(result)
                            )
                error: =>
                    input.removeClass("loading")
                    alert "Server error"
        if @replyCodeTimeout
            clearTimeout(@replyCodeTimeout)
        setTimeout(update, 100)

#
# View for a single page in a document.
#

class btb.EditDocumentPageView extends Backbone.View
    template: _.template $("#editDocumentPage").html()
    events:
        'click .rotate90': 'rotateNinety'
        'click .rotate270': 'rotateTwoSeventy'
        'click .rotateL': 'rotateL'
        'click .rotateR': 'rotateR'
        'click .move-page-up': 'movePageUp'
        'click .move-page-down': 'movePageDown'
        'click .crop': 'crop'
        'click .highlight': 'highlightMe'
        'mousemove .page-image': 'mouseMove'
        'mousedown .page-image': 'mouseDown'

    grabMargin: 4
    scale: 1

    initialize: (options=page: null, pagecount: 1) ->
        @page = options.page
        @page.transformations = @page.transformations or {}
        @pagecount = options.pagecount
        @cropper = new Cropper("black", "rgba(0, 0, 0, 0.5)")
        @highlighter = new Cropper("orange", "rgba(0,0,0,0)")
        @highlighting = true
        @mouseIsDown = false
        # Bind mouseup to document, so we hear it even if the mouse strays out
        # of the canvas.  But filter to avoid redraws.
        $(document).mouseup (event) =>
            if @mouseIsDown
                @mouseUp(event)

    highlightMe: =>
        @setHighlighting(not @highlighting)

    render: =>
        $(@el).html @template(page: @page, pagecount: @pagecount)
        @canvas = $(".page-image", @el)[0]

        # Set active tool
        if @cropping
            $(".crop", @el).addClass("active")
            $(".page-image", @el).css("cursor", "crosshair")
        else if @highlighting
            $(".highlight", @el).addClass("active")
            $(".page-image", @el).css("cursor", "crosshair")
        else
            $(".page-image", @el).css("cursor", "normal")

        # Render canvas
        @img = new Image()
        @img.onload = => @renderCanvas()
        @img.src = @page.scan_page.image
        
        # Hide unusable page sort buttons
        if @pagecount - 1 == @page.order
            $(".move-page-down", @el).hide()
        else if @page.order == 0
            $(".move-page-up", @el).hide()
        this

    renderCanvas: =>
        #
        # Rotation
        #
        theta = (@page.transformations?.rotate or 0) / 360 * 2 * Math.PI
        [w,h] = @page.scan_page.image_dims
        corners = [
            [0, 0]
            [w, 0]
            [0, h]
            [w, h]
        ]
        # rotate corners.
        for c in corners
            [x,y] = c
            c[0] = x * Math.cos(-theta) + y * Math.sin(-theta)
            c[1] = y * Math.cos(-theta) - x * Math.sin(-theta)

        # Get maxima and minima, post rotation.
        minx = _.min _.pluck corners, 0
        miny = _.min _.pluck corners, 1
        maxx = _.max _.pluck corners, 0
        maxy = _.max _.pluck corners, 1

        # Get translation amount: the minima.
        [tx, ty] = [-minx, -miny]
        # Counter-rotate the translation.
        [tx, ty] = [
            tx * Math.cos(theta) + ty * Math.sin(theta),
            ty * Math.cos(theta) - tx * Math.sin(theta),
        ]
        
        scale = Math.min(1, 850 / (maxx - minx))
        # Resize canvas.

        [width, height] = [(maxx - minx) * scale, (maxy - miny) * scale]
        $(@canvas).css({
               width: (width * @scale) + "px"
               height: (height * @scale) + "px"
            }).attr({
               width: width
               height: height
            })

        ctx = @canvas.getContext('2d')
        ctx.clearRect(0, 0, width, height)

        ctx.save()
        ctx.rotate(theta)
        ctx.scale(scale, scale)
        ctx.translate(tx, ty)
        ctx.drawImage(@img, 0, 0)
        ctx.restore()

        #
        # Cropping and highlighting
        #

        if @page.transformations.crop
            @cropper.render(@canvas, @page.transformations.crop, @cropping)
        if @highlight
            @highlighter.render(@canvas, @highlight, @highlighting)


    rotateL: => @_rotate(359)
    rotateR: => @_rotate(1)
    rotateNinety: => @_rotate(90)
    rotateTwoSeventy: => @_rotate(270)
    _rotate: (deg) =>
        oldrot = @page.transformations.rotate or 0
        newrot = (oldrot + deg) % 360
        @page.transformations.rotate = newrot
        if @page.transformations.rotate == 0
            delete @page.transformations.rotate
        @renderCanvas()

    movePageUp: =>
        @trigger "movePageUp"

    movePageDown: =>
        @trigger "movePageDown"

    crop: => @setCropping(not @cropping)

    setCropping: (cropping, trigger=true) =>
        @cropping = cropping
        if @cropping
            @highlighting = false
        @render()
        if trigger
            @trigger "cropping", @cropping


    setHighlighting: (highlighting, trigger=true) =>
        @highlighting = highlighting
        if @highlighting
            @cropping = false
        @render()
        if trigger
            @trigger "highlighting", @highlighting

    mouseDown: (event) =>
        @mouseIsDown = true
        @handleMouse(event, "down")
    mouseUp: (event) =>
        @mouseIsDown = false
        @handleMouse(event, "up")
    mouseMove: (event) => @handleMouse(event, "move")
    handleMouse: (event, type) =>
        offset = $(@canvas).offset()
        mx = (event.pageX - offset.left) / @scale
        my = (event.pageY - offset.top) / @scale
        if @cropping
            orig = @page.transformations.crop
            @page.transformations.crop = @cropper.handleMouse(
                mx, my, type, @page.transformations.crop
            )
            $(@canvas).css("cursor", @cropper.cursor)
            if orig != @page.transformations.crop
                @renderCanvas()
                if @highlight
                    @trigger "highlightChanged", @highlightRelativeToCrop()
        else if @highlighting
            orig = @highlight
            @highlight = @highlighter.handleMouse(
                mx, my, type, @highlight
            )
            $(@canvas).css("cursor", @highlighter.cursor)
            if orig != @highlight
                @renderCanvas()
            if type == 'up'
                @trigger "highlightChanged", @highlightRelativeToCrop()

    clearHighlight: =>
        if @highlight?
            @highlight = null
            @render()

    highlightRelativeToCrop: =>
        if not @page.transformations?.crop?.length > 0
            return @highlight
        [cx, cy, cx1, cy1] = @page.transformations.crop
        [hx, hy, hx1, hy1] = @highlight
        return [
            hx - cx,
            hy - cy,
            Math.min(hx1 - cx, cx1),
            Math.min(hy1 - cy, cy1),
        ]

    setHighlightRelativeToCrop: (crop) =>
        if crop
            [cx, cy, cx1, cy1] = @page.transformations.crop or [0,0,0,0]
            [hx, hy, hx1, hy1] = crop
            @highlight = [hx + cx, hy + cy, hx1 + cx, hy1 + cy]

class Cropper
    grabMargin: 4
    constructor: (@foreground="black", @background="rgba(200, 200, 200, 0.5)") ->
    render: (canvas, crop, cropping) =>
        ctx = canvas.getContext('2d')
        w = canvas.width
        h = canvas.height
        if crop
            [x, y, x1, y1] = crop
            # Shading around four sides
            ctx.fillStyle = @background
            ctx.fillRect(0, 0, x, h)
            ctx.fillRect(x, 0, w-x, y)
            ctx.fillRect(x1, y, w-x1, h-y)
            ctx.fillRect(x, y1, x1-x, h-y1)
            # Border
            ctx.strokeStyle = @foreground
            ctx.lineWidth = 2
            ctx.strokeRect(x, y, x1-x, y1-y)
            if cropping
                # Grab handles
                m = @grabMargin
                ctx.strokeStyle = @foreground
                ctx.strokeRect(x-m, y-m, 2*m, 2*m) # NW
                ctx.strokeRect(x+(x1-x)/2 - m, y-m, 2*m, 2*m) # N
                ctx.strokeRect(x1-m, y-m, 2*m, 2*m) # NE
                ctx.strokeRect(x-m, y+(y1-y)/2 - m, 2*m, 2*m) # E
                ctx.strokeRect(x1-m, y+(y1-y)/2-m, 2*m, 2*m) # W
                ctx.strokeRect(x-m, y1-m, 2*m, 2*m) # SW
                ctx.strokeRect(x + (x1-x)/2 -m, y1-m, 2*m, 2*m) # S
                ctx.strokeRect(x1-m, y1-m, 2*m, 2*m) # SE

    handleMouse: (mx, my, type, crop) =>
        directions = ""
        cursor = ""
        if crop
            m = @grabMargin * 2
            [x,y,x1,y1] = crop
            # Grab handle cursors
            if (x - m) < mx < (x1 + m) and (y - m) < my < (y1 + m)
                # in bounds
                if (y - m) < my < (y + m)
                    directions += "n"
                else if (y1 - m) < my < (y1 + m)
                    directions += "s"
                if (x1 - m) < mx < (x1 + m)
                    directions += "e"
                else if (x - m) < mx < (x + m)
                    directions += "w"
                if directions
                    cursor = "#{directions}-resize"
                else
                    cursor = "move"
                    directions = "+"
        @cursor = cursor or "crosshair"
        if type == "down"
            if crop and not directions
                crop = [mx, my, mx, my]
            @mouseDownState =
                x: mx
                y: my
                directions: directions
                crop: (d for d in crop if crop)
        else if type == "up"
            @mouseDownState = {}
            if crop
                [x, y, x1, y1] = crop
                if x - x1 == 0 or y - y1 == 0
                    return null
        else if type == "move" and @mouseDownState?.x?
            if crop
                [x, y, x1, y1] = crop
            # Creating
            if "" == @mouseDownState.directions
                x = @mouseDownState.x
                y = @mouseDownState.y
                x1 = mx
                y1 = my
            # Moving
            if "+" == @mouseDownState.directions
                [ox, oy, ox1, oy1] = @mouseDownState.crop
                dx = mx - @mouseDownState.x
                dy = my - @mouseDownState.y
                x = ox + dx
                y = oy + dy
                x1 = ox1 + dx
                y1 = oy1 + dy
            # West
            if "w" in @mouseDownState.directions
                x = mx
            # North
            if "n" in @mouseDownState.directions
                y = my
            # East
            if "e" in @mouseDownState.directions
                x1 = mx
            # South
            if "s" in @mouseDownState.directions
                y1 = my
            crop = [
                Math.min(x, x1)
                Math.min(y, y1)
                Math.max(x, x1)
                Math.max(y, y1)
            ]
        return crop

