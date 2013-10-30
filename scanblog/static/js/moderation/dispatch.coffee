class btb.ScanModerationRouter extends Backbone.Router

    routes:
        "": "dashboard"

        "pending":                  "pending"
        "users":                    "users"
        "users/:id":                "users"

        "process":                  "processScanList"
        "process/scan/:id":         "processScan"
        "process/document/:idlist":     "processDocument"

        "mail":                     "mail"
        "mail/:path":               "mail"

        "groups":                   "groups"
        "groups/:type/:id":         "groups"


    _show: (view) =>
        @view?.remove()
        @view = view
        $("#app").html(@view.el)
        @view.render()
        @updateActiveURL()

    updateActiveURL: =>
        path_stub = window.location.hash.split("/")[0..1].join("/")
        $("#subnav a").removeClass "active"
        if path_stub == "" then path_stub = "#"
        $('#subnav a[href="' + path_stub + '"]').addClass "active"

    dashboard:                => @_show(new btb.Dashboard())
    pending:                  => @_show(new btb.PendingScans())
    users:           (userId) => @_show(new btb.UserDetail({userId}))
    mail:              (path) => @_show(new btb.OutgoingMailView({path}))
    processScanList:          => @_show(new btb.ProcessingManager())
    processScan:     (scanId) => @_show(new btb.SplitScanView({scanId}))
    processDocument: (idlist) => @_show(new btb.EditDocumentManager({
        documents: idlist.split(".")
    }))
    groups:        (type, id) => @_show(new btb.GroupManager({type, id}))

btb.app = new btb.ScanModerationRouter()
Backbone.history.start()
