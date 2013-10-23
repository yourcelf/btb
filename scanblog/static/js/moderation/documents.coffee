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
    @documents.fetch({success: @render})
    @docviews = []

  render: =>
    view.remove() for view in @docviews
    @docviews = []

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
        @docviews.push(docview)
    this

  remove: =>
    view.remove() for view in @docviews
    super()

#
# View for a single document, with many pages.
#
class btb.EditDocumentView extends Backbone.View
  template: _.template $("#editDocument").html()
  inReplyToTemplate: _.template $("#editDocumentInReplyTo").html()
  inReplyToCampaignTemplate: _.template $("#editDocumentInReplyToCampaign").html()
  orgChooserTemplate: _.template $("#letterOrgChooser").html()
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
    'click .queue-returned-mail': 'queueReturn'
    'click .queue-refused-mail':  'queueRefuse'
    'click .stow': 'toggleStow'

  initialize: (options=doc: null, num: 1, order: 0) ->
    @doc = options.doc
    @num = options.num
    @order = options.order
    $(window).on "scroll", @stickifyMetadata

  remove: =>
    $(window).off "scroll", @stickifyMetadata
    super()

  stickifyMetadata: =>
    btb.stickyPlace(@$(".metadata"))

  toggleStow: =>
    @$(".metadata").toggleClass("stowed")

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

        pv.bind "redacting", (redacting) =>
          for view in @pageViews
            if view != pv
              view.setRedacting(redacting, false)

        pv.bind "white_redacting", (whiteRedacting) =>
          for view in @pageViews
            if view != pv
              view.setWhiteRedacting(whiteRedacting, false)

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

    userChooser = new btb.InPlaceUserChooser({
      user: new btb.User(@doc.get("author"))
      showState: true
    })
    userChooser.bind "chosen", (model) =>
      @doc.set author: model.toJSON()
    $(".choose-user-holder", @el).append userChooser.render().el
    $(".doc-title", @el).change =>
      @doc.set title: $(".doc-title", @el).val()
    $(".doc-affiliation", @el).on "keyup", @checkAffiliationSlug
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
      val = $(".doc-in-reply-to", @el).val()
      if @doc.get("reply_code") != val
        @doc.set in_reply_to: val
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
        @correspondenceManager = new btb.CorrespondenceManager({
            recipient: new btb.User(@doc.get("author"))
        })
        $(".correspondence-list", @el).html(@correspondenceManager.el)
      when "license"
        $(".user-status-table", @el).html(
          new btb.UserStatusTable(user: new btb.User(@doc.get("author"))).render().el
        )
    if @doc.get("in_reply_to")
      @checkInReplyToCode()

    @$(".queue-return-holder .org-chooser").html(@orgChooserTemplate({
      letter: {recipient: @doc.get("author")}
    }))
    @$(".metadata").css("max-height", $(window).height())
    this

  save: =>
    # validate
    errors = []
    $(".post-save-message", @el).html("")
    if @doc.get("type") == "post" and not @doc.get("highlight_transform")?.crop?.length > 0
      errors.push("Please add a highlighted section to a page.")

    d = btb.strToDate(@doc.get("date_written"))
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

  checkAffiliationSlug: (event) =>
    input = @$(".doc-affiliation")
    details = @$(".doc-affiliation-details")
    val = input.val()
    details.html("")
    if val == ""
      input.removeClass("error")
      input.removeClass("loading")
      @doc.set "affiliation", null
      return
    
    input.addClass("loading")
    clearTimeout @checkAffiliationSlugTimeout if @checkAffiliationSlugTimeout?
    @checkAffiliationSlugTimeout = setTimeout =>
      $.ajax
        url: "/people/affiliations.json"
        type: "GET"
        data:
          slug: val
        success: (data) =>
          input.removeClass "loading"
          if data.pagination.count != 1
            input.addClass("error")
            details.html("Affiliation code not found.")
            @doc.set "affiliation", null
          else
            input.removeClass("error")
            result = data.results[0]
            details.html(result.title)
            @doc.set "affiliation", result
        error: =>
          input.removeClass "loading"
          alert "Server Error"
          window.console?.log?("checkAffiliationSlug", arguments)
    , 100

  checkInReplyToCode: (event) =>
    input = $(".doc-in-reply-to", @el)
    details = $(".doc-in-reply-to-details", @el)
    val = input.val()
    details.html("")
    if val == ""
      input.removeClass("error")
      input.removeClass("loading")
      return
    else if val == @doc.get("reply_code")
      input.addClass("error")
      error = "Can't make a document a reply to itself."
      details.html(@inReplyToTemplate({ error: error, document: null }))
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
          window.console?.log?("checkInReplyToCode", arguments)
    if @replyCodeTimeout
      clearTimeout(@replyCodeTimeout)
    setTimeout(update, 100)

  queueReturn: (event) =>
    @queueDocumentLetter(event, "returned_original")

  queueRefuse: (event) =>
    @queueDocumentLetter(event, "refused_original")

  queueDocumentLetter: (event, type) =>
    event.preventDefault()
    return_holder = @$(".queue-return-holder")
    return_holder.addClass("loading")
    letter = new btb.Letter {
      type: type
      recipient_id: @doc.get("author").id
      document_id: @doc.id
      org_id: $("[name=org_id]", @$(".queue-return-holder")).val()
    }
    letter.save {}, {
      success: =>
        @$(".queue-return-holder").removeClass("loading")
        @$(".queue-return-holder").html("<span class='success'>&check; Return queued.
            <a href='#/users/#{@doc.get("author").id}'>view user\'s correspondence</a>
          </span>")
        @correspondenceManager?.refresh()

      error: =>
        @$(".queue-return-holder").removeClass("loading")
        alert("Server error; return not queued.")
    }

#
# View for a single page in a document.
#

class btb.EditDocumentPageView extends Backbone.View
  template: _.template $("#editDocumentPage").html()
  events:
    'click .rotate90':  'rotateNinety'
    'click .rotate270': 'rotateTwoSeventy'
    'click .rotateL':   'rotateL'
    'click .rotateR':   'rotateR'
    'click .move-page-up':   'movePageUp'
    'click .move-page-down': 'movePageDown'
    'click .crop':    'toggleCropping'
    'click .highlight': 'toggleHighlighting'
    'click .redact':  'toggleRedacting'
    'click .white-redact': 'toggleWhiteRedacting'
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
    @redacter = new MultiCropper("black", "rgba(0, 0, 0, 0)",
                                          "rgba(0, 0, 0, 0.5)")
    @white_redacter = new MultiCropper("#999999", "rgba(0, 0, 0, 0)",
                                                "rgba(255, 255, 255, 0.8)")

    @highlighting = true
    @mouseIsDown = false
    # Bind mouseup to document, so we hear it even if the mouse strays out
    # of the canvas.  But filter to avoid redraws.
    $(document).mouseup (event) =>
      if @mouseIsDown
        @mouseUp(event)

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
    else if @redacting
      $(".redact", @el).addClass("active")
      $(".page-image", @el).css("cursor", "crosshair")
    else if @white_redacting
      $(".white-redact", @el).addClass("active")
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
    if @page.transformations.redactions
      @redacter.render(@canvas, @page.transformations.redactions, @redacting)
    if @page.transformations.white_redactions
      @white_redacter.render(@canvas, @page.transformations.white_redactions, @white_redacting)


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

  movePageUp: => @trigger "movePageUp"
  movePageDown: => @trigger "movePageDown"

  toggleCropping: => @setCropping(not @cropping)
  setCropping: (cropping, trigger=true) =>
    @cropping = cropping
    if @cropping
      @highlighting = false
      @redacting = false
      @white_redacting = false
    @render()
    if trigger
      @trigger "cropping", @cropping

  toggleHighlighting: => @setHighlighting(not @highlighting)
  setHighlighting: (highlighting, trigger=true) =>
    @highlighting = highlighting
    if @highlighting
      @cropping = false
      @redacting = false
      @white_redacting = false
    @render()
    if trigger
      @trigger "highlighting", @highlighting

  toggleRedacting: => @setRedacting(not @redacting)
  setRedacting: (redacting, trigger=true) =>
    @redacting = redacting
    if @redacting
      @cropping = false
      @highlighting = false
      @white_redacting = false
    @render()
    if trigger
      @trigger "redacting", @redacting

  toggleWhiteRedacting: => @setWhiteRedacting(not @white_redacting)
  setWhiteRedacting: (white_redacting, trigger=true) =>
    @white_redacting = white_redacting
    if @white_redacting
      @cropping = false
      @highlighting = false
      @redacting = false
    @render()
    if trigger
      @trigger "white_redacting", @white_redacting

  mouseDown: (event) =>
    @mouseIsDown = true
    @handleMouse(event, "down")
  mouseUp: (event) =>
    @mouseIsDown = false
    @handleMouse(event, "up")
  mouseMove: (event) =>
    @handleMouse(event, "move")
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
      @highlight = @highlighter.handleMouse(mx, my, type, @highlight)
      $(@canvas).css("cursor", @highlighter.cursor)
      if orig != @highlight
        @renderCanvas()
      if type == 'up'
        @trigger "highlightChanged", @highlightRelativeToCrop()
    else if @redacting
      if not @page.transformations.redactions?
        @page.transformations.redactions = []
      has_changed = @redacter.handleMouse(mx, my, type, @page.transformations.redactions)
      $(@canvas).css("cursor", @redacter.cursor)
      if has_changed
        @renderCanvas()
    else if @white_redacting
      if not @page.transformations.white_redactions?
        @page.transformations.white_redactions = []
      has_changed = @white_redacter.handleMouse(mx, my, type, @page.transformations.white_redactions)
      $(@canvas).css("cursor", @white_redacter.cursor)
      if has_changed
        @renderCanvas()

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
  constructor: (@foreground="black",
          @background="rgba(200, 200, 200, 0.5)",
          @interior="rgba(0, 0, 0, 0)") ->
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
      ctx.fillStyle = @interior
      ctx.fillRect(x, y, x1-x, y1-y)
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
        
        # Close handle
        ctx.strokeRect(x1+m, y-5*m, 4*m, 4*m)
        ctx.beginPath()
        ctx.moveTo(x1+m, y-5*m)
        ctx.lineTo(x1+5*m, y-m)
        ctx.stroke()
        ctx.beginPath()
        ctx.moveTo(x1+5*m, y-5*m)
        ctx.lineTo(x1+m, y-m)
        ctx.stroke()

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
      else if (x1 + m/2) <= mx <= (x1 + 5*m/2) and (y - m/2) >= my >= (y - 5*m/2)
        # Inside close handle
        cursor = "pointer"
        directions = "x"
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
      if "x" == @mouseDownState?.directions
        @mouseDownState = {}
        return null
      else
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

class MultiCropper
  grabMargin: 4
  constructor: (@foreground="black",
                @background="rgba(0, 0, 0, 0)",
                @interior="rgba(0, 0, 0, 0.5)") ->

  render: (canvas, crops, cropping) =>
    ctx = canvas.getContext('2d')
    w = canvas.width
    h = canvas.height
    for crop in crops
      [x, y, x1, y1] = crop
      # Shading around four sides
      ctx.fillStyle = @background
      ctx.fillRect(0, 0, x, h)
      ctx.fillRect(x, 0, w-x, y)
      ctx.fillRect(x1, y, w-x1, h-y)
      ctx.fillRect(x, y1, x1-x, h-y1)
      ctx.fillStyle = @interior
      ctx.fillRect(x, y, x1-x, y1-y)
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

        # Close handle
        ctx.strokeRect(x1+m, y-5*m, 4*m, 4*m)
        ctx.beginPath()
        ctx.moveTo(x1+m, y-5*m)
        ctx.lineTo(x1+5*m, y-m)
        ctx.stroke()
        ctx.beginPath()
        ctx.moveTo(x1+5*m, y-5*m)
        ctx.lineTo(x1+m, y-m)
        ctx.stroke()

  handleMouse: (mx, my, type, crops) =>
    match = null
    if @mouseDownState?.match?
      match = @mouseDownState.match
    else
      matches = []
      m = @grabMargin * 2
      _.each crops, (crop, i) =>
        directions = ""
        cursor = ""
        [x, y, x1, y1] = crop
        if (x - m) < mx < (x1 + m) and (y - m) < my < (y1 + m)
          # Inside shape
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
        else if (x1 + m/2) <= mx <= (x1 + 5*m/2) and (y - m/2) >= my >= (y - 5*m/2)
          # Inside close handle
          cursor = "pointer"
          directions = "x"
        if directions
          matches.push({
            cursor: cursor
            crop: crop
            index: i
            directions: directions
          })

      # pick the best match
      if matches.length > 0
        matches.sort (a, b) ->
          # Directional matches take precedence over whole object moves 
          if a.directions != "+" and b.directions == "+"
            return -1
          else if a.directions == "+" and b.directions != "+"
            return 1
          else
            # If they're both the same type, pick the smaller.
            [ax0, ay0, ax1, ay1] = a.crop
            a_size = Math.abs((ax1 - ax0) * (ay1 - ay0))
            [bx0, by0, bx1, by1] = b.crop
            b_size = Math.abs((bx1 - bx0) * (by1 - by0))
            if a_size < b_size
              return -1
            else if b_size < a_size
              return 1
            else
              return 0
        match = matches[0]
      @cursor = match?.cursor or "crosshair"

    if type == "down"
      unless match?
        match =
          crop: null
          directions: ""
          index: crops.length
      @mouseDownState =
        x: mx
        y: my
        match: match
    else if type == "move" and @mouseDownState?.x?
      if @mouseDownState.match.crop?
        [x, y, x1, y1] = @mouseDownState.match.crop
      # Creating
      if "" == @mouseDownState.match.directions
        x = @mouseDownState.x
        y = @mouseDownState.y
        x1 = mx
        y1 = my
        @mouseDownState.match.crop = [x, y, x1, y1]
      # Moving
      if "+" == @mouseDownState.match.directions
        [ox, oy, ox1, oy1] = @mouseDownState.match.crop
        dx = mx - @mouseDownState.x
        dy = my - @mouseDownState.y
        x = ox + dx
        y = oy + dy
        x1 = ox1 + dx
        y1 = oy1 + dy
      if "w" in @mouseDownState.match.directions
        x = mx
      if "n" in @mouseDownState.match.directions
        y = my
      if "e" in @mouseDownState.match.directions
        x1 = mx
      if "s" in @mouseDownState.match.directions
        y1 = my
      crops[@mouseDownState.match.index] = [
        Math.min(x, x1)
        Math.min(y, y1)
        Math.max(x, x1)
        Math.max(y, y1)
      ]
      return true
    else if type == "up"
      if "x" == @mouseDownState?.match?.directions
        if @mouseDownState.match.index < crops.length
          crops.splice(@mouseDownState.match.index, 1)
          @mouseDownState = {}
          return true
      @mouseDownState = {}
    return false

