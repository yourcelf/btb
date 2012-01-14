# vim: set ts=4:sw=4
class btb.PendingScan extends Backbone.Model
    url: ->
        stub = if @get("id") then "/" + @get("id") else ""
        btb.PendingScanList.prototype.baseUrl + stub

class btb.PendingScanList extends btb.FilteredPaginatedCollection
    model: btb.PendingScan
    baseUrl: "/scanning/pendingscans.json"
    comparator: (ps) ->
        return -( new Date(ps.get "created").getTime() )

class btb.PendingScans extends btb.PaginatedView
    template: _.template $("#pendingScanList").html()
    itemTemplate: _.template $("#pendingScanItem").html()
    events:
        'click span.pagelink': 'turnPage'
        'click input.pending-scan-missing': 'pendingScanMissing'
        'click .remove-pending-scan': 'removePendingScan'
        'click .show-missing': 'showMissing'
        'click .show-pending': 'showPending'

    initialize: ->
        @pendingScanList = new btb.PendingScanList
        @pendingScanList.filter.per_page = 6
        @showPending()

    render: =>
        $(@el).html @template
            orgs: btb.ORGANIZATIONS
        userChooser = new btb.UserSearch
        userChooser.bind "chosen", (user) => @addPendingScan(user)
        $(".user-chooser-holder", @el).html userChooser.render().el
        @renderItems()
        this

    renderItems: =>
        $(".pending-scan-list .item", @el).remove()
        if @pendingScanList.length == 0
            $(".pending-scan-list", @el).hide()
        else
            $(".pending-scan-list", @el).show()
        @pendingScanList.each (ps) =>
            row = $ @itemTemplate
                pendingscan: ps.toJSON()
            rendered = $(".pending-scan-list", @el).append row
            author = new btb.User ps.get("author")
            uc = new btb.UserCompact({user: author}).render().el
            $(".user-compact", row).html(uc)

        @renderPagination @pendingScanList, $(".pagination", @el)
        this

    fetchItems: =>
        @pendingScanList.fetch {success: => @renderItems()}

    addPendingScan: (user) ->
        @pendingScanList.create {
            author_id: user.get "id"
            org_id: $("[name=org_id]", @el).val()
        }, {
            success: (model) => @render()
        }
        

    removePendingScan: (event) =>
        ps = @pendingScanList.get(
            parseInt($("input.pending-scan-id", event.currentTarget).val())
        )
        @pendingScanList.remove(ps)
        ps.destroy { success: => @render() }

    pendingScanMissing: (event) =>
        ps = @pendingScanList.get(
            $(".pending-scan-id", $(event.currentTarget).parent()).val()
        )
        gone = $(event.currentTarget).is(":checked")
        ps.save {missing: if gone then 1 else 0 },
            success: (model) ->
            error: ->
                alert "Server error"
                

    turnPage: (event) =>
        @pendingScanList.filter.page = @newPageFromEvent event
        @setPageLoading()
        @fetchItems()

    showMissing: (event) =>
        psl = @pendingScanList
        delete psl.filter.pending if psl.filter.pending?
        $(".show-pending", @el).removeClass("chosen")
        psl.filter.missing = 1
        $(".show-missing", @el).addClass("chosen")
        @fetchItems()

    showPending: (event) =>
        psl = @pendingScanList
        delete psl.filter.missing if psl.filter.missing?
        $(".show-missing", @el).removeClass("chosen")
        psl.filter.pending = 1
        $(".show-pending", @el).addClass("chosen")
        @fetchItems()


