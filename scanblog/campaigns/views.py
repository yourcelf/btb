import json

from django.http import HttpResponseBadRequest, Http404
from django.db import transaction, IntegrityError

from btb.utils import JSONView, permission_required_or_deny, args_method_decorator

from campaigns.models import Campaign
from profiles.models import Organization
from annotations.models import ReplyCode

class Not200Exception(Exception):
    pass

class CampaignsJSON(JSONView):
    @permission_required_or_deny("campaigns.change_campaign")
    def get(self, request):
        campaigns = Campaign.objects.org_filter(request.user)
        if 'id' in request.GET:
            return self.get_by_id(request, campaigns)
        return self.paginated_response(request, campaigns)

    @permission_required_or_deny("campaigns.change_campaign")
    def put(self, request):
        attrs = json.loads(request.body)
        try:
            campaign = Campaign.objects.org_filter(request.user).get(pk=attrs.get('id'))
        except Campaign.DoesNotExist:
            raise Http404
        return self.update_attrs(request, campaign, attrs)

    @permission_required_or_deny("campaigns.change_campaign")
    def post(self, request):
        attrs = json.loads(request.body)
        campaign = Campaign()
        return self.update_attrs(request, campaign, attrs)

    @permission_required_or_deny("campaigns.change_campaign")
    def delete(self, request):
        attrs = json.loads(request.body)
        try:
            campaign = Campaign.objects.org_filter(request.user).get(pk=attrs['id'])
        except Campaign.DoesNotExist:
            raise Http404
        if campaign.reply_code.document_replies.exists():
            urls = []
            for reply in campaign.reply_code.document_replies.all():
                urls.append(reply.get_edit_url())
            return self.error("The following documents are replies to this campaign. Their in-reply-to field must be cleared or changed before this campaign can be deleted:\n{0}".format(
                "\n".join(urls)
            ))
        else:
            campaign.delete()
        return self.json_response({"status": "success"})

    def update_attrs(self, request, campaign, attrs):
        # With Django > 1.6, this is the cleanest way we have to do what we
        # used to do with 'commit_on_success'.
        try:
            with transaction.atomic():
                res = self._update_attrs(request, campaign, attrs)
                if res.status_code != 200:
                    raise Not200Exception()
        except Not200Exception:
            pass
        return res

    def _update_attrs(self, request, campaign, attrs):
        missing = []
        for key in ["title", "slug", "body", "organizations",
                    "reply_code", "public", "ended"]:
            if key not in attrs:
                missing.append(key)
        if missing:
            return self.error("Missing parameters: {0}".format(", ".join(missing)))
        orgs = []
        for org_dict in attrs['organizations']:
            try:
                org = Organization.objects.org_filter(request.user).get(pk=org_dict['id'])
            except Organization.DoesNotExist:
                return self.error("Organization {0} not found or not allowed.".format(
                    org_dict['id']))
            orgs.append(org)
        if not orgs:
            return self.error("No organization specified.") 
        if Campaign.objects.filter(slug=attrs['slug']).exclude(pk=attrs.get('id')).exists():
            return self.error("Slug not unique.")

        for key in ["title", "slug", "body", "public", "ended"]:
            setattr(campaign, key, attrs[key])
        # Update reply code.
        try:
            orig_reply_code = campaign.reply_code
        except ReplyCode.DoesNotExist:
            orig_reply_code = None
        if orig_reply_code:
            if orig_reply_code.code != attrs['reply_code']:
                orig_reply_code.code = attrs['reply_code']
                try:
                    orig_reply_code.save()
                except IntegrityError:
                    return self.error("Reply code not available.")
        else:
            reply_code, created = ReplyCode.objects.get_or_create(code=attrs['reply_code'])
            if not created:
                return self.error("Reply code not available.")
            campaign.reply_code = reply_code

        campaign.save()


        # Update organizations.
        campaign.organizations = orgs
        return self.json_response(campaign.to_dict())

    def error(self, msg):
        return HttpResponseBadRequest(json.dumps({"error": msg}))
