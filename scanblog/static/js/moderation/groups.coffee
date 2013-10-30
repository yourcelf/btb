class IdModel extends Backbone.Model
  url: => @baseUrl + "?id=#{@get("id")}"

class btb.Organization extends IdModel
  baseUrl: "/people/orgs.json"

class btb.OrganizationList extends btb.FilteredPaginatedCollection
  model: btb.Organization
  baseUrl: btb.Organization.prototype.baseUrl

class btb.Affiliation extends IdModel
  baseUrl: "/people/affiliations.json"

class btb.AffiliationList extends btb.FilteredPaginatedCollection
  model: btb.Affiliation
  baseUrl: btb.Affiliation.prototype.baseUrl

class btb.Campaign extends IdModel
  baseUrl: "/campaigns/campaigns.json"

class btb.CampaignList extends btb.FilteredPaginatedCollection
  model: btb.Campaign
  baseUrl: btb.Campaign.prototype.baseUrl

class btb.GroupManager extends Backbone.View
