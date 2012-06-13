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

    dashboard: =>
        $("#app").html(
            new btb.Dashboard().render().el
        )
        @updateActiveURL()

    pending: =>
        $("#app").html(
            new btb.PendingScans().render().el
        )
        @updateActiveURL()

    users: (userId) =>
        $("#app").html(
            new btb.UserDetail( { userId: userId }).render().el
        )
        @updateActiveURL()

    processScanList: () =>
        $("#app").html(
            new btb.ProcessingManager().render().el
        )
        @updateActiveURL()

    processScan: (scanId) =>
        $("#app").html(
            new btb.SplitScanView(scanId).render().el
        )
        @updateActiveURL()

    processDocument: (idlist) =>
        $("#app").html(
            new btb.EditDocumentManager(documents: idlist.split(".")).render().el
        )
        @updateActiveURL()

    mail: (path) =>
        $("#app").html(
            new btb.OutgoingMailView(path).render().el
        )
        @updateActiveURL()

    updateActiveURL: =>
        path_stub = window.location.hash.split("/")[0..1].join("/")
        $("#subnav a").removeClass "active"
        if path_stub == "" then path_stub = "#"
        $('#subnav a[href="' + path_stub + '"]').addClass "active"

btb.app = new btb.ScanModerationRouter()
Backbone.history.start()
