from btb.utils import JSONView, permission_required_or_deny

class CampaignsJSON(JSONView):
    @permission_required_or_deny("campaigns.change_campaign")
    def get(self, request):
        pass

    @permission_required_or_deny("campaigns.change_campaign")
    def put(self, request):
        pass

    @permission_required_or_deny("campaigns.change_campaign")
    def post(self, request):
        pass

    @permission_required_or_deny("campaigns.change_campaign")
    def delete(self, request):
        pass
