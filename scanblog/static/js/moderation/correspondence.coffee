#
# Models and collections
#
class btb.Comment extends Backbone.Model
class btb.CommentList extends Backbone.Collection

class btb.Letter extends Backbone.Model
    url: =>
        baseUrl = btb.LetterList.prototype.baseUrl
        if @get("id") then baseUrl + "/" + @get("id") else baseUrl

class btb.LetterList extends btb.FilteredPaginatedCollection
    model: btb.Letter
    baseUrl: "/correspondence/letters.json"
    parse: (response) ->
        @counts = response.counts
        super response

class btb.Correspondence extends Backbone.Model

class btb.CorrespondenceList extends btb.FilteredPaginatedCollection
    model: btb.Correspondence
    baseUrl: "/correspondence/correspondence.json"

class btb.Mailing extends Backbone.Model
    url: =>
        baseUrl = btb.MailingList.prototype.baseUrl
        if @get("id") then baseUrl + "/" + @get("id") else baseUrl

class btb.MailingList extends btb.FilteredPaginatedCollection
    model: btb.Mailing
    baseUrl: "/correspondence/mailings.json"

class btb.NeededLetters extends Backbone.Model
    url: =>
        base = "/correspondence/needed_letters.json"
        if @get "consent_form_cutoff"
            return base + "?" + $.param consent_form_cutoff: @get "consent_form_cutoff"
        return base


#
# Views
#

# A menu for adding letters of particular types.  Requires a {recipientId: id}
# as an argument.
# 
# Triggers:
#   "letterAdded", letter: when a letter is added
#   "editLetter": requesting an external editor to edit a custom letter.
class btb.LetterAddingMenu extends Backbone.View
    template: _.template $("#letterMenu").html()
    events:
        'change select.type-chooser': 'addLetter'

    initialize: (options={}) ->
        @recipient = options.recipient

    render: =>
        $(@el).html @template recipient: @recipient.toJSON()

    showLoading: => $(".loading", @el).show()
    hideLoading: => $(".loading", @el).hide()

    addLetter: (event) =>
        @showLoading()
        type = $(event.currentTarget).val()
        letter = new btb.Letter
            recipient: @recipient.toJSON()
            org_id: $(".org_id", @el).val()
            type: type
        if type == "letter"
            # For custom letters, trigger the need for an external editor.
            $(".org-chooser", @el).hide()
            @trigger "editLetter", letter
        else if type != ""
            # For form letters, save straight away.
            letter.save {}, {
                success: (model, response) =>
                    @hideLoading()
                    @render()
                    @trigger "letterAdded", model
            }

# A form for editing a custom letter. Requires the {recipientId: id}
#
# Triggers:
#   "letterAdded", letter: when a letter is saved
#   "cancelled": when letter editing is cancelled by the user
class btb.LetterEditor extends Backbone.View
    template: _.template $("#letterEditor").html()
    orgTemplate: _.template $("#letterOrgChooser").html()
    events:
        'click .enqueue-letter': 'enqueue'
        'click .cancel': 'cancel'

    initialize: (options={}) ->
        @letter = options.letter
        unless @letter.get("recipient")?.organizations
            recipient = new btb.User(id: @letter.get("recipient_id"))
            recipient.fetch
                success: (model) =>
                    @letter.set(recipient: model)
                    @renderOrgs()
                error: => alert "Server error #{recpient.url()}"
        this

    cancel: => @trigger "cancelled"
    showLoading: => $(".loading", @el).show()
    hideLoading: => $(".loading", @el).hide()

    render: =>
        $(@el).html @template
            letter: @letter.toJSON()
        @renderOrgs()
        this

    renderOrgs: =>
        $(".org-chooser", @el).html @orgTemplate
            letter: @letter.toJSON()

    enqueue: =>
        @showLoading()
        @letter.set
            body: $(".letter-body", @el).val()
            org_id: $(".org_id", @el).val()
            send_anonymously: not $(".not-anonymous", @el).is(":checked")
        @letter.save {}, {
            success: (model, response) =>
                @hideLoading()
                @trigger "letterAdded", model
                @type = ""
                @letter = null
                $(".custom-letter").remove()
            error: (model, response) =>
                $(".letter-error", @el)
                    .html(_.escapeHTML(response.responseText))
                    .addClass("error")
                alert "Server error #{@letter.url()}"

        }
        
    
# A table showing comments attached to a letter.
class btb.CommentsMailingTable extends Backbone.View
    heading: _.template $("#commentHeading").html()
    template: _.template $("#commentRow").html()
    initialize: (options) ->
        if options.modelParams
            @collection = new btb.CommentList _.map options.modelParams, (c) ->
                new btb.Comment(c)
        else
            @collection = new btb.CommentList
    render: =>
        $(@el).html @heading()
        for comment in @collection.models
            $(@el).append @template comment: comment.toJSON()
        this

class btb.LetterRow extends Backbone.View
    template: _.template $("#letterRow").html()
    specialHandlingTemplate: _.template $("#specialHandlingDialog").html()
    events:
        'click .edit-letter': 'editLetter'
        'click .resend-letter': 'resendLetter'
        'click .delete-letter': 'deleteLetter'
        'click .mark-letter-sent': 'markLetterSent'
        'click .mark-letter-unsent': 'markLetterUnsent'
        'click .special-handling': 'specialHandling'

    initialize: (letter) ->
        @letter = letter

    editLetter: (event) => @trigger "editLetter", @letter
    
    # Enqueues a new letter copied from the given one.
    resendLetter: (event) =>
        @showLoading()
        copy = @letter.clone()
        copy.save {"id": null, "sent": null, "created": undefined},
            success: (model) =>
                @hideLoading()
                @trigger "letterAdded", model
            error: => alert "Server error #{copy.url()}"
        
    # Marks the given letter as 'sent' at time Now.
    markLetterSent: (event) =>
        @showLoading()
        @letter.save {"sent": true},
            success: (model) =>
                @hideLoading()
                @trigger "letterChanged", model
                @render()
            error: => alert "Server error #{@letter.url()}"

    # Sets the 'sent' field to null.
    markLetterUnsent: (event) =>
        @showLoading()
        @letter.save {"sent": null},
            success: (model) =>
                @hideLoading()
                @trigger "letterChanged", model
                @render()
            error: => alert "Server error #{@letter.url()}"
    
    # Goodbye letter!
    deleteLetter: (event) =>
        @showLoading()
        @letter.destroy
            success: () =>
                @hideLoading()
                @trigger "letterDeleted", @letter
            error: => alert "Server error #{@letter.url()}"

    specialHandling: (event) =>
        div = @specialHandlingTemplate(letter: @letter.toJSON())
        $(div).dialog
            modal: true
            width: 500
            height: 300
            title: "Special mail handling instructions"

    showLoading: =>
        $(".not-loading", @el).hide()
        $(".loading", @el).show()
    hideLoading: =>
        $(".not-loading", @el).show()
        $(".loading", @el).hide()

    render: =>
        $(@el).html @template
            letter: @letter.toJSON()
            commaddress: @letter.get("org")?.mailing_address.replace(/\n/g, ", ")
        if @letter.get("type") == "comments"
            # Add a comments table...
            commentsTable = new btb.CommentsMailingTable
                modelParams: @letter.get "comments"
            $(".comments-table", @el).html commentsTable.render().el
        this

class btb.CorrespondenceScanRow extends Backbone.View
    template: _.template $("#correspondenceScanRow").html()
    initialize: (scan) ->
        @scan = scan

    render: =>
        $(@el).html @template scan: @scan.toJSON()
        this
    

#
# A table of just letters.
#
class btb.LetterTable extends btb.PaginatedView
    template: _.template $("#letterTableHeading").html()
    events:
        'click span.pagelink': 'turnPage'

    initialize: (options={filter: {}}) ->
        @collection = new btb.LetterList
        @collection.filter = options.filter

    render: =>
        $(@el).html @template()
        for letter in @collection.models
            row = new btb.LetterRow letter
            row.bind "editLetter", (letter) =>
                @trigger "editLetter", letter
            row.bind "letterDeleted", (letter) =>
                @fetchItems()
            $(@el).append row.render().el
        @addPaginationRow(true, true)
        $(@el).addClass("letter-table")
        this
    showLoading: => $(".fetch-loading", @el).show()
    hideLoading: => $(".fetch-loading", @el).hide()

    addPaginationRow: (bottom=true, top=false) =>
        if @collection.length == 0
            $(@el).append("<div class='row'>No results</div>")
        else if @collection.pagination?
            if bottom
                pag = $("<div class='pagination'></div>")
                $(@el).append(pag)
                @renderPagination @collection, pag
            if top
                pag = $("<div class='pagination'></div>")
                $(@el).prepend(pag)
                @renderPagination @collection, pag
        this
    
    fetchItems: () =>
        @showLoading()
        @collection.fetch
            success: =>
                @hideLoading()
                @trigger "lettersFetched"
                @render()
            error: => alert "Server errror #{@collection.url()}"

    turnPage: (event) =>
        @collection.filter.page = @newPageFromEvent event
        @setPageLoading()
        @collection.fetch
            success: =>
                @render()
            error: => alert "Server error #{@collection.url()}"


#
# A tabular, paginated view of LetterRow and CorrespondenceScanRow instances.
#
class btb.CorrespondenceTable extends btb.LetterTable
    initialize: (options={filter: {}}) ->
        @collection = new btb.CorrespondenceList
        @collection.filter = options.filter

    render: =>
        $(@el).html @template()
        @collection.each (obj) =>
            if obj.get("letter")?
                row = new btb.LetterRow(new btb.Letter obj.get "letter")
                
                # Bind events that change number of rows.
                for event in ["letterAdded", "letterDeleted"]
                    row.bind event, (model) =>
                        @fetchItems()
                # Bubble up edit events.
                row.bind "editLetter", (letter) =>
                    @trigger "editLetter", letter

            else if obj.get("scan")?
                row = new btb.CorrespondenceScanRow(new btb.Scan obj.get "scan")

            $(@el).append row.render().el
        @addPaginationRow()
        $(@el).addClass("letter-table")
        this

# 
# Holder for a letter adder/editor and correspondence table that work together.
#
class btb.CorrespondenceManager extends Backbone.View
    initialize: (options) ->
        @recipient = options.recipient

        @table = new btb.CorrespondenceTable
            filter: { user_id: @recipient.id, per_page: 5}
        @table.bind "editLetter", (letter) => @editLetter(letter)
        @table.fetchItems()

        @adder = new btb.LetterAddingMenu recipient: @recipient
        @adder.bind "letterAdded", (letter) => @table.fetchItems()
        @adder.bind "editLetter", (letter) => @editLetter(letter)

        $(@el).html(@adder.el)
        $(@el).append(@table.el)
        @render()

    render: =>
        @adder.render()
        @table.render()
        this

    editLetter: (letter) =>
        editor = new btb.LetterEditor { letter: letter, orgs: @userOrgs }
        $(@adder.el).append editor.render().el
        editor.bind "cancelled", => @adder.render() # erase editor
        editor.bind "letterAdded", (letter) =>
            @adder.render() # erase editor
            @table.fetchItems()



class btb.MailingBuilder extends Backbone.View
    template: _.template $("#buildMailing").html()
    events:
        'change .consent-form-cutoff': 'fetchItems'
        'change .filters input[type=checkbox]': 'updateCounts'
        'click input[name=build_mailing]': 'buildMailing'

    initialize: ->
        @needed = new btb.NeededLetters
        @fetchItems()

    getCutoff: => return $(".consent-form-cutoff", @el).val()
    setCutoff: (val) => $(".consent-form-cutoff", @el).val(val)

    fetchItems: =>
        $(@el).show()
        @showLoading()
        @needed.set "consent_form_cutoff": @getCutoff() or undefined
        @needed.fetch
            success: (model) =>
                @needed = model
                @hideLoading()
                @updateCounts()
            error: => alert "Server error #{@needed.url()}"

    render: =>
        $(@el).html @template()
        $(".consent-form-cutoff", @el).datepicker
            dateFormat: 'yy-mm-dd'
        this

    showLoading: => $(".loading", @el).show()
    hideLoading: => $(".loading", @el).hide()
    
    updateCounts: =>
        counts = @needed.toJSON()
        total = 0
        possible = 0
        $(".choice", @el).hide()
        for name, count of counts
            count = parseInt(count)
            if count > 0
                $(".choice.#{name}", @el).show()
                $(".choice.#{name} .count", @el).html(_.escapeHTML(count))
                if $("input[name=#{name}]", @el).is(":checked")
                    total += count
                possible += count
        $(".total-count", @el).html(total)
        if possible == 0
            $(@el).hide()
        if total == 0
            $("input[name=build_mailing]", @el).attr("disabled", "disabled")
        else
            $("input[name=build_mailing]", @el).removeAttr("disabled")
        # Special case for date filter
        if @getCutoff()
            $(".choice.consent_form", @el).show()

    buildMailing: =>
        types = []
        cutoff = @getCutoff()
        for input in $("input[type=checkbox]:checked", @el)
            types.push $(input).attr "name"
        mailing = new btb.Mailing
        @showLoading()
        mailing.save {types: types, consent_cutoff: cutoff},
            success: (model) =>
                @hideLoading()
                @setCutoff("")
                @trigger "mailingAdded", (model)
                @fetchItems()
            error: => alert "Server errror #{mailing.url()}"
            

class btb.LetterFilter extends Backbone.View
    template: _.template $("#letterFilters").html()
    events:
        'change input[type=checkbox]': 'chooseType'
        'keyup  input[type=text]'    : 'chooseSearch'
    initialize: ->
        @filter = {}

    showLoading: => $("input[type=text]", @el).addClass "loading"
    hideLoading: => $("input[type=text]", @el).removeClass "loading"

    render: =>
        $(@el).html @template()
        this

    chooseType: =>
        types = []
        for input in $(".filters input:checked[type=checkbox]", @el)
            types.push $(input).attr "name"
        @filter.types = types.join(",")
        @trigger "filterChanged", @filter

    chooseSearch: =>
        txt = $("input[type=text]", @el).val()
        if not txt and @filter.text?
            delete @filter.text
        @filter.text = txt
        @trigger "filterChanged", @filter

    updateCounts: (counts) =>
        $(".choice", @el).hide()
        for name, count of counts
            name = name or "other"
            if count > 0
                $("span.#{name} .count", @el).html(_.escapeHTML(count))
                $(".choice.#{name}", @el).show()

class btb.MailingFilter extends btb.PaginatedView
    template: _.template $("#mailingFilters").html()
    events:
        'click .all': 'chooseAll'
        'click .all-sent': 'chooseAllSent'
        'click .all-unsent': 'chooseAllUnsent'
        'click .enqueued': 'chooseEnqueued'

    initialize: ->
        @collection = new btb.MailingList
        @fetchItems()

    render: =>
        $(@el).html @template()
        @items = {}
        for mailing in @collection.models
            item = new btb.MailingFilterItem mailing
            item.bind "itemSelected", @chooseItem
            item.bind "itemDeleted", (item) =>
                @fetchItems()
                @trigger "itemDeleted", (item)
            item.bind "itemChanged", @chooseItem



            $(".mailings", @el).append item.render().el
            @items[mailing.get "id"] = item
        this

    showLoading: => $(".loading", @el).show()
    hideLoading: => $(".loading", @el).hide()

    fetchItems: =>
        @showLoading()
        @collection.fetch
            success: =>
                @render()
                @trigger "mailingsLoaded"
                @hideLoading()
            error: => alert "Server error #{@collection.url()}"
    deselect: =>
        @filter = {}
        $("li", @el).removeClass("selected")
    chooseEnqueued: =>
        @deselect()
        $("li.enqueued", @el).addClass("selected")
        @filter.mailing_id = null
        @filter.unsent = 1
        @trigger "filterChanged", @filter
        btb.app.navigate "#/mail"
        this
    chooseAll: =>
        @deselect()
        $("li.all", @el).addClass("selected")
        @trigger "filterChanged", @filter
        btb.app.navigate "#/mail/all"
        this
    chooseAllSent: =>
        @deselect()
        @filter.sent = 1
        $("li.all-sent", @el).addClass("selected")
        @trigger "filterChanged", @filter
        btb.app.navigate "#/mail/sent"
        this
    chooseAllUnsent: =>
        @deselect()
        $("li.all-unsent", @el).addClass("selected")
        @filter.unsent = 1
        @trigger "filterChanged", @filter
        btb.app.navigate "#/mail/unsent"
        this
    chooseItem: (item) =>
        if not isNaN item
            item = @items[item]
        if not item
            return @chooseEnqueued()
        @deselect()
        $(item.el).addClass("selected")
        @filter.mailing_id = item.mailing.get "id"
        @trigger "filterChanged", @filter
        btb.app.navigate "#/mail/#{@filter.mailing_id}"
        this

class btb.MailingFilterItem extends Backbone.View
    template: _.template $("#mailingFilterItem").html()
    tagName: 'li'
    events:
        'click .item': 'selectItem'
        'click .delete': 'deleteItem'
        'click .mark-sent': 'markSent'
        'click .mark-unsent': 'markUnsent'
        'click .clear-cache': 'clearCache'

    initialize: (mailing) ->
        @mailing = mailing
    render: =>
        $(@el).html @template mailing: @mailing.toJSON()
        if @mailing.get("date_finished")
            $(@el).removeClass "unsent"
        else
            $(@el).addClass "unsent"
        this
    selectItem: =>
        @trigger "itemSelected", this
    deleteItem: =>
        @showLoading()
        @mailing.destroy
            success: =>
                @hideLoading()
                @trigger "itemDeleted", @mailing
            error: => alert "Server errror #{@mailing.url()}"
    showLoading: =>
        $(".loading", @el).show()
        $(".not-loading", @el).hide()
    hideLoading: =>
        $(".loading", @el).hide()
        $(".not-loading", @el).show()

    markSent: => @change(date_finished: true)
    markUnsent: => @change(date_finished: null)
    clearCache: =>
        @showLoading()
        $.ajax
            url: "/correspondence/clear_cache/" + @mailing.get("id")
            type: "POST"
            success: =>
                @hideLoading()
            error: (jqXHR, textStatus, errorThrown) =>
                alert "Server error: #{textStatus}"
    change: (updates) =>
        @showLoading()
        @mailing.save updates, {
            success: (model) =>
                @mailing = model
                @trigger "itemChanged", this
                @render()
        }
            
          

class btb.OutgoingMailView extends Backbone.View
    template: _.template $("#outgoingMail").html()
    initialize: (path) ->
        @letters = new btb.LetterTable
        @letterFilter = new btb.LetterFilter
        @mailingFilter = new btb.MailingFilter
        @builder = new btb.MailingBuilder

        @letters.bind "editLetter", (letter) => @editLetter(letter)
        @letters.bind "lettersFetched", =>
            @letterFilter.updateCounts @letters.collection.counts
            @letterFilter.hideLoading()

        @letterFilter.bind "filterChanged", @delayedFetchLetters
        @mailingFilter.bind "filterChanged", @fetchLetters
        @mailingFilter.bind "itemDeleted", =>
            @fetchLetters()
            @builder.fetchItems()

        @builder.bind "mailingAdded", (mailing) =>
            goToNewOne = =>
                @mailingFilter.chooseItem mailing.get "id"
                @mailingFilter.unbind "mailingsLoaded", goToNewOne
            @mailingFilter.bind "mailingsLoaded", goToNewOne
            @mailingFilter.fetchItems()

        navigateCallback = =>
            switch path
                when "all" then @mailingFilter.chooseAll()
                when "sent" then @mailingFilter.chooseAllSent()
                when "unsent" then @mailingFilter.chooseAllUnsent()
                else
                    if not isNaN path
                        @mailingFilter.chooseItem parseInt path
                    else
                        @mailingFilter.chooseEnqueued()
            @mailingFilter.unbind "mailingsLoaded", navigateCallback
        @mailingFilter.bind "mailingsLoaded", navigateCallback
        this

    editLetter: (letter) =>
        editor = new btb.LetterEditor { letter: letter }
        editor.bind "letterAdded", (letter) =>
            @letters.fetchItems()
        editor.bind "cancelled", =>
            $(editor.el).remove()
        $(@letters.el).prepend editor.render().el

    render: =>
        $(@el).html @template()
        $(".letter-filter", @el).html @letterFilter.render().el
        $(".letters", @el).html @letters.render().el
        $(".mailing-filter", @el).html @mailingFilter.render().el
        $(".build-mailing", @el).html @builder.render().el
        this

    fetchLetters: =>
        @letterFilter.showLoading()
        @letters.collection.filter = _.extend {}, @letterFilter.filter, @mailingFilter.filter
        @letters.fetchItems()

    delayedFetchLetters: =>
        @letterFilter.showLoading()
        if @_fetchLetterDelay?
            clearTimeout @_fetchLetterDelay
        @_fetchLetterDelay = setTimeout(@fetchLetters, 100)

