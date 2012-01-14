class btb.Dashboard extends Backbone.View
    template: _.template $("#dashboard").html()
    events:
        "click .doc-chooser span": "changeDocs"
        "click .scan-chooser span": "changeScans"

    initialize: ->
        @docsView = new btb.ProcessDocListView()
        @lettersView = new btb.DashboardNeededLettersView()
        @scansView = new btb.ProcessScanListView()
        @ticketsView = new btb.NoteManager({
            filter:
              unresolved: 1
              sort: "-important,created"
            addable: false
        })

    render: =>
        $(@el).html @template()
        $(".open-tickets", @el).html @ticketsView.el
        $(".outgoing-mail", @el).html @lettersView.render().el
        $(".open-scans", @el).html @scansView.render().el
        $(".open-documents", @el).html @docsView.render().el
        $(".doc-chooser span[data-status=#{ @docsView.list.filter.status }]", @el).addClass("chosen")
        $(".scan-chooser span[data-complete=#{ @scansView.list.filter.processing_complete }]", @el).addClass("chosen")
        return this

    changeDocs: (event) =>
        $(".doc-chooser span", @el).removeClass("chosen")
        $(event.currentTarget).addClass("chosen")
        @docsView.list.filter.status = $(event.currentTarget).attr("data-status")
        @docsView.fetch()

    changeScans: (event) =>
        $(".scan-chooser span", @el).removeClass("chosen")
        $(event.currentTarget).addClass("chosen")
        @scansView.list.filter.processing_complete = $(event.currentTarget).attr("data-complete")
        @scansView.fetch()


class btb.DashboardNeededLettersView extends Backbone.View
    template: _.template $("#dashboardLetters").html()
    itemTemplate: _.template $("#dashboardLettersItem").html()
    initialize: ->
        @needed = new btb.NeededLetters()
        @queued = new btb.LetterList
        @queued.filter =
            page: 1
            per_page: 1
            unsent: 1
        @queued.fetch
            success: =>
                @render()
            error: =>
                alert "Server Error: Queued Letters"

        @needed.fetch
            success: =>
                @render()
            error: =>
                alert "Server Error: NeededLetters"

    render: =>
        $(@el).html @template( enqueuedCount: @queued.pagination.count )
        for type,count of @needed.toJSON()
            if count > 0
                $(".needed-list", @el).append @itemTemplate {
                    type: type.split("_").join(" ")
                    count: count
                }
        this
        
