class IdModel extends Backbone.Model
  url: => @baseUrl + "?id=#{@get("id")}"

class btb.Organization extends IdModel
  type: "organization"
  baseUrl: "/people/organizations.json"
  defaults: ->
    return {
      id: undefined
      public: false
      name: ""
      slug: ""
      about: ""
      footer: ""
      mailing_address: ""
      personal_contact: ""
      custom_intro_packet_url: null
      outgoing_mail_handled_by: {}
      moderators: new btb.UserList()
      members: new btb.UserList()
    }

  parse: (data) =>
    for key in ["members", "moderators"]
      if data[key]?
        members = new btb.UserList()
        members.add((new btb.User(member) for member in data[key]))
        data[key] = members
    return data

  # Return true if this is a full copy of the model, and not a "light" copy.
  isFull: => return @get("members")?

class btb.OrganizationList extends btb.FilteredPaginatedCollection
  model: btb.Organization
  baseUrl: btb.Organization.prototype.baseUrl

class btb.Affiliation extends IdModel
  type: "affiliation"
  baseUrl: "/people/affiliations.json"

class btb.AffiliationList extends btb.FilteredPaginatedCollection
  model: btb.Affiliation
  baseUrl: btb.Affiliation.prototype.baseUrl

class btb.Campaign extends IdModel
  type: "campaign"
  baseUrl: "/campaigns/campaigns.json"

class btb.CampaignList extends btb.FilteredPaginatedCollection
  model: btb.Campaign
  baseUrl: btb.Campaign.prototype.baseUrl

###
  GroupManager
--------------------------------------------------------------------------
| OrgListView   | OrgDetailView/AffiliationDetailView/CampaignDetailView |
|               |                                                        |
|               |  OrgModeratorCtrl  | OrgMemberCtrl |  OrgFieldsCtrl    |
| OrgAdder      |                    |               |                   |
|---------------|                    |               |                   |
| Affiliation   |                    |               |                   |
|  ListView     |                    |               |                   |
|               |                    |               |                   |
|AffiliationAdder                    |               |                   |
|---------------|                    |               |                   |
| CampaignList  |                    |               |                   |
|  View         |                    |               |                   |
|               |                    |               |    --------       |
|               |                    |               |    | SAVE |       |
| CampaignAdder |                    |               |    --------       |
-------------------------------------------------------------------------
###

class btb.GroupManager extends Backbone.View
  template: _.template $("#groupManagerTemplate").html()
  initialize: (options) ->
    @org_list = new btb.OrganizationList()
    @aff_list = new btb.AffiliationList()
    @camp_list = new btb.CampaignList()

    @org_list_view = new btb.OrganizationListView({collection: @org_list})
    @aff_list_view = new btb.AffiliationListView({collection: @aff_list})
    @camp_list_view = new btb.CampaignListView({collection: @camp_list})

    @org_adder_view = new btb.GroupAdderView({collection: @org_list})
    @aff_adder_view = new btb.AffiliationAdderView({collection: @aff_list})
    @camp_adder_view = new btb.CampaignAdderView({collection: @camp_list})

    @org_detail = new btb.OrganizationDetailView()
    @aff_detail = new btb.AffiliationDetailView()
    @camp_detail = new btb.CampaignDetailView()

    for view in [@org_adder_view, @aff_adder_view, @camp_adder_view,
                 @org_list_view, @aff_list_view, @camp_list_view]
      @listenTo view, "choose", @set_detail

    @type = options.type
    @id = parseInt(options.id)
    unless @type and @id and !isNaN(@id)
      @type = "organization"
      @id = 1

    for list in [@org_list, @aff_list, @camp_list]
      if list.model.prototype.type == @type
        list.fetch({
          success: (list) =>
            @set_detail(list.get(@id))
        })
      else
        list.fetch()

  remove: =>
    super()
    for view in [@org_list_view, @aff_list_view, @camp_list_view,
                 @org_adder_view, @aff_adder_view, @camp_adder_view,
                 @org_detail, @aff_detail, @camp_detail]
      view.remove()

  _set_initial_model: =>
     
  set_detail: (model) =>
    for list in [@org_list_view, @aff_list_view, @camp_list_view]
      list.unset()
    list = null
    detail = null
    switch model.type
      when "organization" then [list, detail] = [@org_list_view, @org_detail]
      when "affiliation" then [list, detail] = [@aff_list_view, @aff_detail]
      when "campaign" then [list, detail] = [@camp_list_view, @camp_detail]
    list.set_model(model)
    detail.set_model(model)
    @$(".detail").html(detail.el)
    detail.render()
    detail.delegateEvents()
    @type = model.type
    @id = model.id
    btb.app.navigate("/groups/#{@type}/#{@id}")

  render: =>
    @$el.html(@template())

    @$(".org-list-view").html(@org_list_view.el)
    @$(".org-adder-view").html(@org_adder_view.el)
    @$(".aff-list-view").html(@aff_list_view.el)
    @$(".aff-adder-view").html(@aff_adder_view.el)
    @$(".camp-list-view").html(@camp_list_view.el)
    @$(".camp-adder-view").html(@camp_adder_view.el)

    @org_list_view.render()
    @org_adder_view.render()
    @aff_list_view.render()
    @aff_adder_view.render()
    @camp_list_view.render()
    @camp_adder_view.render()

class btb.GroupListView extends Backbone.View
  template: _.template $("#groupListTemplate").html()
  events:
    'click .item': 'triggerItem'

  initialize: ({collection}) ->
    @collection = collection
    @listenTo collection, "add remove change", @render

  triggerItem: (event) =>
    @trigger "choose", @collection.get($(event.currentTarget).attr("data-cid"))

  set_model: (model) =>
    @unset()
    if model.type == @collection.model.prototype.type
      @$("[data-cid=#{model.cid}]").addClass("active")
      @model = model

  unset: =>
    @model = null
    @$(".active").removeClass("active")

  render: =>
    @$el.html(@template(@context()))
    @set_model(@model) if @model

class btb.GroupAdderView extends Backbone.View
  template: _.template $("#groupAdderTemplate").html()
  events:
    'click a.adder': 'startAdding'

  initialize: ({collection}) ->
    @collection = collection

  render: =>
    @$el.html(@template())

  startAdding: (event) =>
    event.preventDefault()
    model = new @collection.model
    @collection.add(model)
    @trigger "choose", model


class btb.OrganizationListView extends btb.GroupListView
  context: =>
    return {
      title: "Organizations"
      items: ({cid: o.cid, title: o.get("name") or "[New org]"} for o in @collection.models)
    }

class btb.OrganizationDetailView extends Backbone.View
  template: _.template $("#organizationDetailTemplate").html()
  events:
    'click .html-preview':  'htmlPreview'
    'keyup #slug_control':  'checkSlug'
    'keyup #name_control':  'checkName'
    'click .save':          'save'
    'click .delete':        'delete'

  initialize: (options) =>
    @model = options?.model

  checkSlug: (event) =>
    val = @$("#slug_control").val()
    good = /^[-a-z0-9]+$/g.test(val)
    @$("#slug_control").toggleClass("error", not good)

  checkName: (event) =>
    @$("#name_control").toggleClass("error", not @$("#name_control").val())

  checkModerators: (event) =>
    if @moderator_list.collection.length + @moderator_list.additions.length == 0
      @$(".members-column").prepend(
        "<div class='error'>Must specify at least one moderator.</div>"
      )
    else
      @$(".members-column .error").remove()

  save: (event) =>
    event.preventDefault()
    @checkSlug()
    @checkName()
    @checkModerators()
    if @$(".error").length > 0
      @$(".error").parent()[0].scrollIntoView()
      return
    @$(".save").addClass("loading")
    @$(".status").html("")
    @model.set({
      public: @$("#public_control").is(":checked")
      name: @$("#name_control").val()
      slug: @$("#slug_control").val()
      personal_contact: @$("#personal_contact_control").val()
      # This is a hack to sanitize the HTML -- use the dom parser to
      # close/strip straggling tags, etc.
      about: $("<div>#{@$("#about_control").val()}</div>").html()
      footer: $("<div>#{@$("#footer_control").val()}</div>").html()
      mailing_address: @$("#mailing_address_control").val()
      outgoing_mail_handler: {id: @$("#outgoing_mail_handler_control").val()}
      replacement_org: @$("#replacement_org_control").val()
      moderators: @moderator_list.collection
      members: @member_list.collection
    })
    for model in @moderator_list.additions.models
      @model.get("moderators").add(model)
    for model in @member_list.additions.models
      @model.get("members").add(model)
    #TODO: Handle file uploads and removals.
    @model.save {}, {
      success: (model) =>
        @$(".save").removeClass("loading")
        @render()
        @$(".status").html("Saved successfully.")
        btb.app.navigate("/groups/organization/#{model.id}")

      error: (model, xhr, options) =>
        console.error(xhr, xhr.responseText)
        @$(".save").removeClass("loading")
        @$(".status").addClass("error").html("Error saving.")
        @$(".satus").append(xhr.responseText)
    }

  delete: (event) =>
    event.preventDefault()
    dialog = @$(".delete-confirmation")
    dialog.dialog({
      modal: true
      buttons: {
        "Delete organization": =>
          receiving_org = $("#delete_org_replacement").val()
          @model.destroy {
            data: JSON.stringify({
              destination_organization: receiving_org
              id: @model.id
            })
            processData: false
            success: =>
              dialog.dialog("close")
              btb.app.navigate("/groups/organization/#{receiving_org}", {trigger: true})
            error: =>
              alert("Server error")
          }
        "Cancel": =>
          dialog.dialog("close")
      }
    })


  set_model: (model) =>
    @model = null
    if model.type == "organization"
      unless model.isNew()
        model.fetch {
          success: (model) =>
            @model = model
            @render()
        }
      else
        @model = model
        @render()
    else
      @render()

  htmlPreview: (event) =>
    event.preventDefault()
    html = $("##{$(event.currentTarget).attr("data-source")}").val()
    div = $("<div>#{html}</div>")
    div.dialog({
      modal: true,
      close: -> div.remove()
      open: (event, ui) ->
        $(".ui-widget-overlay").bind('click', -> div.dialog('close'))
    })

  render: =>
    if @model and (@model.isFull() or @model.isNew())
      @$el.html(@template(@model.toJSON()))
      @moderator_list?.remove()
      @moderator_list = new OrganizationUserList({
        collection: @model.get("moderators")
        filter: {in_org: false, blogger: false}
      })
      @$(".moderator-list").html(@moderator_list.el)
      @moderator_list.render()
      @moderator_list.additions.on "add remove", @checkModerators
      @moderator_list.collection.on "add remove", @checkModerators

      @member_list?.remove()
      @member_list = new OrganizationUserList({
        collection: @model.get("members")
        filter: {in_org: true, blogger: true}
      })

      @member_list.collection.on "add remove", =>
        @$(".replacement-org-control").toggle(@member_list.removals.length > 0)

      @$(".member-list").html(@member_list.el)
      @member_list.render()
    else
      @$el.html("<img src='/static/img/spinner.gif' alt='Loading...' />")

class OrganizationUserList extends Backbone.View
  template: _.template $("#organizationUserListTemplate").html()
  events:
    'click .remove': 'toggleUser'
    'click .restore': 'toggleUser'

  initialize: ({collection, filter}) =>
    @collection = collection
    @additions = new btb.UserList
    @removals = new btb.UserList
    @filter = filter

  render: =>
    @collection.cssclass = "current"
    @additions.cssclass = "added"
    @removals.cssclass = "removed"
    @$el.html(@template({
      collection: @collection
      additions: @additions
      removals: @removals
    }))
    @search?.remove()
    @search = new btb.UserSearch({filter: @filter})
    @search.on "chosen", @addUser
    @$(".user-search-holder").html(@search.el)
    @search.render()

  toggleUser: (event) =>
    user_id = $(event.currentTarget).attr("data-user-id")
    if @additions.get(user_id)?
      user = @additions.get(user_id)
      @additions.remove(user)
    else if @removals.get(user_id)?
      user = @removals.get(user_id)
      @removals.remove(user)
      @collection.add(user)
    else
      user = @collection.get(user_id)
      @removals.add(user)
      @collection.remove(user)
    @triggerChanged()
    @render()

  addUser: (model) =>
    if @collection.get(model.id) or @additions.get(model.id)
      @triggerChanged()
      @render()
      return
    else if @removals.get(model.id)
      @removals.remove(model)
      @collection.add(model)
      @triggerChanged()
      @render()
    else
      @additions.add(model)
      @triggerChanged()
      @render()

  triggerChanged: =>
    @trigger "changeset", {removals: @removals, additions: @additions}

class btb.AffiliationListView extends btb.GroupListView
  context: => {items: [], title: "Affiliations"}

class btb.AffiliationAdderView extends btb.GroupAdderView
class btb.AffiliationDetailView extends Backbone.View
  template: _.template $("#affiliationDetailTemplate").html()
  render: =>
    @$el.html(@template())

class btb.CampaignListView extends btb.GroupListView
  context: => {items: [], title: "Campaigns"}
class btb.CampaignAdderView extends btb.GroupAdderView
class btb.CampaignDetailView extends Backbone.View
  template: _.template $("#campaignDetailTemplate").html()
  render: =>
    @$el.html(@template())
