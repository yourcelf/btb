class btb.Note extends Backbone.Model
    url: =>
        baseUrl = btb.NoteList.prototype.baseUrl
        if @get("id")
            baseUrl + "/" + @get("id")
        else
            baseUrl
class btb.NoteList extends btb.FilteredPaginatedCollection
    model: btb.Note
    baseUrl: "/annotations/notes.json"

# A single row for NoteViewTable.
class btb.NoteView extends Backbone.View
    template: _.template $("#noteRow").html()
    events:
        'click .delete-note': 'deleteNote'
        'click .edit-note': 'editNote'
        'click .mark-resolved': 'markResolved'
    initialize: (note) -> @note = note
    render: =>
        $(@el).html @template note: if @note? then @note.toJSON() else {}
        this
    deleteNote: (event) =>
        if confirm("Really delete this note?  There's no undo.")
            $(".loading", @el).show()
            @note.destroy
                success: =>
                    $(".loading", @el).hide()
                    @trigger "noteDeleted", @note
    editNote: (event) =>
        @trigger "editNote", @note
    markResolved: (event) =>
        $(".loading", @el).show()
        @note.save {"resolved": 1}, {
            success: (model) =>
                $(".loading", @el).hide()
                @render()
            error: =>
                $(".loading", @el).hide()
                alert("Server error -- changes not saved")
        }
            
#
# A view displaying a list of notes.  Takes an options hash with one
# property:
#   filter: {} a hash of properties to filter the collection of notes
#              fetched from the server.
#
class btb.NoteViewTable extends btb.PaginatedView
    events:
        'click span.pagelink': 'turnPage'
        'change select.per-page': 'setPerPage'

    initialize: (options={filter: {}}) ->
        @collection = new btb.NoteList
        @collection.filter = options.filter
        @collection.filter.per_page or= 6
        @fetchItems()
        $(@el).addClass("note-table")
        @hideForSinglePage = true

    render: =>
        $(@el).html("")
        for model in @collection.models
            view = new btb.NoteView(model)
            
            # Bubble up editNote event
            view.bind "editNote", (note) =>
                @trigger "editNote", note
            
            # Re-fetch on delete
            view.bind "noteDeleted", (note) =>
                @fetchItems()

            $(@el).append view.render().el

        pag = $("<div class='pagination'></div>")
        $(@el).append pag
        @renderPagination(@collection, pag)
        # Remove self-links
        $(".note-obj-link", @el).each (i, link) =>
            if $(link).attr("href") == window.location.pathname + window.location.hash
                $(link).remove()
        this

    turnPage: (event) =>
        @collection.filter.page = @newPageFromEvent(event)
        @fetchItems()

    setPerPage: (event) =>
        event.preventDefault()
        @collection.filter.per_page = $(event.currentTarget).val()
        @fetchItems()

    fetchItems: =>
        $(@el).addClass("loading")
        @setPageLoading()
        @collection.fetch
            success: =>
                $(@el).removeClass("loading")
                @render()
            error: =>
                $(@el).removeClass("loading")
                alert "Server error"

#
# A view drawing a form for editing and adding notes.  Takes an options dict
# with a property:
#
#   defaults: {} a hash of default properties for new notes (e.g. user_id,
#                scan_id, etc)
#
class btb.NoteEditor extends Backbone.View
    template: _.template $("#noteEditor").html()
    events:
        'click .add-note': 'addNote'
        'click .save-note': 'saveNote'
        'click .cancel-add': 'cancel'

    initialize: (options={defaults: {}}) =>
        @defaults = options.defaults
        @addable = (not options.addable?) or options.addable

    render: =>
        $(@el).html @template
            note: if @note? then @note.toJSON() else null
            addable: @addable
        
    addNote: (event) =>
        @note = new btb.Note @defaults
        @render()

    cancel: (event) =>
        @note = null
        @render()

    saveNote: (event) =>
        $(".loading", @el).show()

        if $("input[name=needsResolution]", @el).is(":checked")
            resolved = null
        else
            resolved = true
        @note.save {
                text: $("textarea[name=text]", @el).val()
                important: $("input[name=important]", @el).is(":checked")
                resolved: resolved
            }, {
                success: (model) =>
                    $(".loading", @el).hide()
                    @trigger "noteAdded", model
                    @cancel()

                error: (model) =>
                    alert "Server error"
                    $(".loading", @el).hide()
            }
    startEditing: (note) =>
        @note = note
        @render()

#
# Combined button for adding notes, and a table listing notes.
# Invoke with an options dict that contains two parameters:
#   filter: {} a hash of properties to filter the note table by 
#              (e.g. user_id, document_id)
#
#   default: {} a hash of default properties for new notes.
#
class btb.NoteManager extends Backbone.View
    initialize: (options={}) ->
        @table = new btb.NoteViewTable options
        @editor = new btb.NoteEditor options
        @render()
        $(@el).html(@editor.el)
        $(@el).append(@table.el)

        @editor.bind "noteAdded", (note) =>
            @table.fetchItems()
        @table.bind "editNote", (note) =>
            @editor.startEditing(note)

    render: =>
        @editor.render()
        @table.render()
        this
