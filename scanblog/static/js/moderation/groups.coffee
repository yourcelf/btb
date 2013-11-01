class IdModel extends Backbone.Model
  url: => @baseUrl + "?id=#{@get("id")}"

class btb.Organization extends IdModel
  type: "organization"
  baseUrl: "/people/organizations.json"

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
|               |   OrgModeratorCtrl | OrgMemberCtrl |  OrgFieldsCtrl    |
| OrgAdder      |                    |               |                   |
|---------------|                    |               |                   |
| Affiliation   |                    |               |                   |
|  ListView     |                    |               |                   |
|               |                    |               |                   |
| AffiliationAdder                   |               |                   |
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
    @org_list = new btb.OrganizationList
    @aff_list = new btb.AffiliationList
    @camp_list = new btb.CampaignList

    @org_list_view = new btb.OrganizationListView({collection: @org_list})
    @aff_list_view = new btb.AffiliationListView({collection: @aff_list})
    @camp_list_view = new btb.CampaignListView({collection: @camp_list})

    @org_adder_view = new btb.OrganizationAdderView({collection: @org_list})
    @aff_adder_view = new btb.AffiliationAdderView({collection: @aff_list})
    @camp_adder_view = new btb.CampaignAdderView({collection: @camp_list})

    @org_detail = new btb.OrganizationDetailView()
    @aff_detail = new btb.AffiliationDetailView()
    @camp_detail = new btb.CampaignDetailView()

    for view in [@org_adder_view, @aff_adder_view, @camp_adder_view,
                 @org_list_view, @aff_list_view, @camp_list_view]
      @listenTo view, "choose", @set_detail

    @type = options.type
    @id = options.id
    unless @type and @id
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
    console.log "set_detail", model
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
    @trigger "choose", @collection.get(parseInt($(event.currentTarget).attr("data-id")))

  set_model: (model) =>
    @unset()
    if model.type == @collection.model.prototype.type
      @$("[data-id=#{model.id}]").addClass("active")

  unset: =>
    @$(".active").removeClass("active")

  render: =>
    @$el.html(@template(@context()))

class btb.GroupAdderView extends Backbone.View
  template: _.template $("#groupAdderTemplate").html()
  events:
    'click a.adder': 'startAdding'

  render: =>
    @$el.html(@template())

  startAdding: (event) =>
    event.preventDefault()


class btb.OrganizationListView extends btb.GroupListView
  context: =>
    return {
      title: "Organizations"
      items: ({id: o.id, title: o.get("name")} for o in @collection.models)
    }

class btb.OrganizationAdderView extends btb.GroupAdderView
class btb.OrganizationDetailView extends Backbone.View
  template: _.template $("#organizationDetailTemplate").html()
  initialize: (options) =>


  set_model: (model) =>
    if model.type == "organization"
      @model = model
      @model.fetch {success: @render}
    else
      @model = null
      @render()

  render: =>
    if @model
      @$el.html(@template(@model.toJSON()))
    else
      @$el.html("<img src='/static/img/spinner.gif' alt='Loading...' />")

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
