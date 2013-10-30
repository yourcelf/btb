import os
import json
import datetime

from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.core.urlresolvers import reverse

from profiles.models import Profile, Organization

from scanning.models import Document, Scan
from annotations.models import Note
from btb.tests import BtbLoginTestCase
from comments.models import Comment, Favorite

class TestUrls(TestCase):
    fixtures = ["initial_data.json"]
    def testAbsoluteUrls(self):
        u = User.objects.create(username="hoopla", pk=12345)
        u.profile.display_name = "Test User"
        u.profile.blogger = True
        u.save()
        self.assertEquals(u.profile.get_absolute_url(), "/people/show/12345")
        self.assertEquals(u.profile.get_blog_url(), "/blogs/12345/test-user")
        self.assertEquals(u.profile.get_bare_blog_url(), "/blogs/12345/")


class TestProfileManager(TestCase):
    fixtures = ["initial_data.json"]
    def setUp(self):
        # Remove default user from fixture.
        User.objects.get(username='uploader').delete()
        sender = User.objects.create(username="sender")
        def create_letter(recipient, ltype, sent):
            recipient.received_letters.create(
                sender=sender, 
                type=ltype, 
                sent=datetime.datetime.now() if sent else None
            )
        profiles = {
            'sender': sender.profile,
            'active_commenter': User.objects.create(
                username="active_commenter").profile,
            'inactive_commenter': User.objects.create(
                username="inactive_commenter", is_active=False).profile,
        }

        # User.is_active bit
        for active in [True, False]:
            # Profile.consent_form_received bit
            for consented in [True, False]:
                # Create letter objects with sent=None?
                for unsent_letters in [True, False]:
                    # Create consent_form letter?
                    for consent_form in [True, False]:
                        for waitlist in [True, False]:
                            key = (active, consented, unsent_letters, 
                                    consent_form, waitlist)
                            key = tuple([{True: 1, False: 0}[s] for s in key])

                            user = User.objects.create(
                                    username=",".join(str(k) for k in key),
                                    is_active=active)
                            user.profile.consent_form_received = consented
                            user.profile.blogger = True
                            user.profile.managed = True
                            user.profile.save()
                            if consent_form or unsent_letters:
                                create_letter(user, 'consent_form', 
                                              consent_form)
                            if waitlist or unsent_letters:
                                create_letter(user, "waitlist", waitlist)

                            profiles[key] = user.profile

        self.profiles = profiles
        self.sender = sender

    def assertQsContains(self, qs, profile_list):
        self.assertEquals(
            set(list(qs)), 
            set([self.profiles[p] for p in profile_list])
        )

    def test_active(self):
        self.assertQsContains(Profile.objects.active(), [
            "sender",
            "active_commenter",
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 1, 1, 1, 1,),
            (1, 1, 1, 1, 0,),
            (1, 1, 1, 0, 1,),
            (1, 1, 0, 1, 1,),
            (1, 0, 1, 1, 1,),
            (1, 1, 1, 0, 0,),
            (1, 1, 0, 1, 0,),
            (1, 0, 1, 1, 0,),
            (1, 1, 0, 0, 1,),
            (1, 0, 1, 0, 1,),
            (1, 0, 0, 1, 1,),
            (1, 1, 0, 0, 0,),
            (1, 0, 1, 0, 0,),
            (1, 0, 0, 1, 0,),
            (1, 0, 0, 0, 1,),
            (1, 0, 0, 0, 0,),
        ])
    def test_inactive(self):
        self.assertQsContains(Profile.objects.inactive(), [
            "inactive_commenter",
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (0, 1, 1, 1, 1,),
            (0, 1, 1, 1, 0,),
            (0, 1, 1, 0, 1,),
            (0, 1, 0, 1, 1,),
            (0, 0, 1, 1, 1,),
            (0, 1, 1, 0, 0,),
            (0, 1, 0, 1, 0,),
            (0, 0, 1, 1, 0,),
            (0, 1, 0, 0, 1,),
            (0, 0, 1, 0, 1,),
            (0, 0, 0, 1, 1,),
            (0, 1, 0, 0, 0,),
            (0, 0, 1, 0, 0,),
            (0, 0, 0, 1, 0,),
            (0, 0, 0, 0, 1,),
            (0, 0, 0, 0, 0,),
        ])
    def test_inactive_commenters(self):
        self.assertQsContains(Profile.objects.inactive_commenters(), [
            "inactive_commenter",
        ])
    def test_inactive_bloggers(self):
        self.assertQsContains(Profile.objects.inactive_bloggers(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (0, 1, 1, 1, 1,),
            (0, 1, 1, 1, 0,),
            (0, 1, 1, 0, 1,),
            (0, 1, 0, 1, 1,),
            (0, 0, 1, 1, 1,),
            (0, 1, 1, 0, 0,),
            (0, 1, 0, 1, 0,),
            (0, 0, 1, 1, 0,),
            (0, 1, 0, 0, 1,),
            (0, 0, 1, 0, 1,),
            (0, 0, 0, 1, 1,),
            (0, 1, 0, 0, 0,),
            (0, 0, 1, 0, 0,),
            (0, 0, 0, 1, 0,),
            (0, 0, 0, 0, 1,),
            (0, 0, 0, 0, 0,),
        ])

    def test_commenters(self):
        self.assertQsContains(Profile.objects.commenters(), [
            "sender",
            "active_commenter",
        ])
    def test_bloggers(self):
        self.assertQsContains(Profile.objects.bloggers(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 1, 1, 1, 1,),
            (1, 1, 1, 1, 0,),
            (1, 1, 1, 0, 1,),
            (1, 1, 0, 1, 1,),
            (1, 0, 1, 1, 1,),
            (1, 1, 1, 0, 0,),
            (1, 1, 0, 1, 0,),
            (1, 0, 1, 1, 0,),
            (1, 1, 0, 0, 1,),
            (1, 0, 1, 0, 1,),
            (1, 0, 0, 1, 1,),
            (1, 1, 0, 0, 0,),
            (1, 0, 1, 0, 0,),
            (1, 0, 0, 1, 0,),
            (1, 0, 0, 0, 1,),
            (1, 0, 0, 0, 0,),
        ])
    def test_enrolled(self):
        self.assertQsContains(Profile.objects.enrolled(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 1, 1, 1, 1,),
            (1, 1, 1, 1, 0,),
            (1, 1, 1, 0, 1,),
            (1, 1, 0, 1, 1,),
            (1, 1, 1, 0, 0,),
            (1, 1, 0, 1, 0,),
            (1, 1, 0, 0, 1,),
            (1, 1, 0, 0, 0,),
        ])
    def test_invited(self):
        self.assertQsContains(Profile.objects.invited(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 0, 1, 1, 1,),
            (1, 0, 1, 1, 0,),
            (1, 0, 0, 1, 1,),
            (1, 0, 1, 0, 1,),
            (1, 0, 0, 1, 0,),
            (1, 0, 1, 0, 0,),
        ])
    def test_invitable(self):
        self.assertQsContains(Profile.objects.invitable(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 0, 0, 0, 1,),
            (1, 0, 0, 0, 0,),
        ])
    def test_waitlisted(self):
        self.assertQsContains(Profile.objects.waitlisted(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 0, 0, 0, 1,),
        ])
    def test_waitlistable(self):
        self.assertQsContains(Profile.objects.waitlistable(), [
            # active, consented, unsent_letters, consent_form_sent, waitlist_sent
            (1, 0, 0, 0, 0,),
        ])

    def test_needs_signup_complete_letter(self):
        # With no letters in the test set, all enrolled folks need signup complete.
        self.assertEqual(set(Profile.objects.needs_signup_complete_letter()), 
                         set(Profile.objects.enrolled()))
        # Add a letter, and the user shouldn't be in needs_signup_complete anymore.
        p = Profile.objects.enrolled()[0]
        p.user.received_letters.create(
                sender=self.sender,
                type="signup_complete")

        self.assertTrue(p not in set(Profile.objects.needs_signup_complete_letter()))

    def test_needs_first_post_letter(self):
        # No one needs one yet, as no one has a post.
        self.assertEqual(set(Profile.objects.needs_first_post_letter()), set())

        p = Profile.objects.enrolled()[0]
        p.user.documents_authored.create(type="post", editor=self.sender, 
                status="published")
        self.assertTrue(p in Profile.objects.needs_first_post_letter())

        # Create a first post letter, then no one should need one again.
        p.user.received_letters.create(
                sender=self.sender,
                type="first_post")
        self.assertEqual(set(Profile.objects.needs_first_post_letter()), set())

    def test_needs_comments_letter(self):
        # No one needs one yet, as there are no posts or comments.
        self.assertEqual(set(Profile.objects.needs_comments_letter()), set())

        # Add a post...
        p = Profile.objects.enrolled()[0]
        doc = p.user.documents_authored.create(type="post", editor=self.sender,
                status="published")
        # ... still no one.
        self.assertEqual(set(Profile.objects.needs_comments_letter()), set())

        # Add a comment...
        comment = doc.comments.create(user=self.sender, comment="My Comment")
        # ... now we need one:
        self.assertTrue(p in set(Profile.objects.needs_comments_letter()))

        # Create a comment letter ...
        cl = p.user.received_letters.create(
                sender=self.sender,
                type="comments")
        cl.comments.add(comment)
        # ... and no one should need one anymore.
        self.assertEqual(set(Profile.objects.needs_comments_letter()), set())

    def test_bloggers_with_published_content(self):
        self.assertEqual(set(Profile.objects.bloggers_with_published_content()), set())
        has_post, has_profile, has_both, has_nothing = Profile.objects.enrolled()[0:4]
        has_post.user.documents_authored.create(type="post", editor=self.sender, 
                status="published")
        has_profile.user.documents_authored.create(type="profile", editor=self.sender,
                status="published")
        has_both.user.documents_authored.create(type="post", editor=self.sender, 
                status="published")
        has_both.user.documents_authored.create(type="profile", editor=self.sender,
                status="published")

        self.assertEqual(
            sorted(Profile.objects.bloggers_with_published_content(), key=lambda a: a.pk),
            sorted([has_post, has_profile, has_both], key=lambda a: a.pk)
        )

class TestOrgPermissions(TestCase):
    fixtures = ["initial_data.json"]
    def setUp(self):
        self.orgs = []
        self.superuser = User.objects.create(username="superuser", is_superuser=True)
        self.superuser.set_password("superuser")
        self.superuser.save()
        for i in range(2):
            org = Organization.objects.create(name="Org %s" % i, slug="org-%s" % i)
            member = User.objects.create(username="org%smember" % i)
            member.profile.display_name = "Org %s Member" % i
            member.profile.blogger = True
            member.profile.managed = True
            member.profile.consent_form_received = True
            member.profile.save()
            org.members.add(member)
            mod = User.objects.create(username="org%smod" % i)
            mod.set_password("mod")
            mod.save()
            mod.groups.add(Group.objects.get(name="moderators"))
            org.moderators.add(mod)
            self.orgs.append({
                'org': org,
                'member': member,
                'mod': mod,
            })
        self.orgs[1]['org'].outgoing_mail_handled_by = self.orgs[0]['org']
        self.orgs[1]['org'].save()

    def _org_vars(self):
        return (self.orgs[0]['org'], 
                self.orgs[0]['mod'], 
                self.orgs[0]['member'],
                self.orgs[1]['org'], 
                self.orgs[1]['mod'], 
                self.orgs[1]['member'])


    def _json_results(self, username, password, url, id_set):
        self.client.logout()
        self.assertTrue(
            self.client.login(username=username, password=password)
        )
        res = self.client.get(url)
        self.assertEquals(res.status_code, 200)
        struct = json.loads(res.content)
        result_ids = set(a['id'] for a in struct['results'])
        self.assertEquals(result_ids, id_set)

    def test_access_notes(self):
        org0, mod0, member0, org1, mod1, member1 = self._org_vars()

        def note_permissions(note, can_edit, cant_edit, filtr=None):
            self.assertTrue(note in Note.objects.all().org_filter(can_edit))
            self.assertFalse(note in Note.objects.all().org_filter(cant_edit))
            if filtr:
                self.assertTrue(note in Note.objects.filter(**filtr).org_filter(can_edit))
                self.assertFalse(note in Note.objects.filter(**filtr).org_filter(cant_edit))

        # Basic permissions

        doc = Document.objects.create(author=member0, editor=mod0)
        doc_note = doc.notes.create(creator=mod0)
        note_permissions(doc_note, mod0, mod1, {'document__isnull': False})

        scan = Scan.objects.create(author=member0, uploader=mod0, pdf="foo")
        scan_note = scan.notes.create(creator=mod0)
        note_permissions(scan_note, mod0, mod1, {'scan__isnull': False})

        user_note = member0.notes.create(creator=mod0)
        note_permissions(user_note, mod0, mod1, {"user__isnull": False})

        # JSON access

        # Moderator for group 0, or superuser
        for u, p in ((mod0.username, "mod"), ("superuser", "superuser")):
            self._json_results(u, p, 
                "/annotations/notes.json", 
                set([doc_note.id, scan_note.id, user_note.id]))
            self._json_results(u, p, 
                "/annotations/notes.json?user_id=%s" % user_note.user.id,
                set([user_note.id]))
            self._json_results(u, p, 
                "/annotations/notes.json?scan_id=%s" % scan_note.scan.id,
                set([scan_note.id]))
            self._json_results(u, p, 
                "/annotations/notes.json?document_id=%s" % doc_note.document.id,
                set([doc_note.id]))
        # Moderator for group 1
        self.assertFalse(org0 in mod1.organizations_moderated.all())
        self._json_results(mod1.username, "mod",
                "/annotations/notes.json", set([]))

    def test_access_documents(self):
        org0, mod0, member0, org1, mod1, member1 = self._org_vars()

        doc = Document.objects.create(author=member0, editor=mod0)
        self.assertEquals(
            set(Document.objects.org_filter(mod0)),
            set([doc])
        )
        self.assertEquals(
            set(Document.objects.org_filter(mod1)),
            set()
        )

        # JSON access

        c = self.client
        for u, p in ((mod0.username, "mod"), ("superuser", "superuser")):
            self._json_results(u, p,
                    "/scanning/documents.json",
                    set([doc.pk]))
        self._json_results(mod1.username, "mod", 
                "/scanning/documents.json", 
                set())
    
    def test_access_scans(self):
        org0, mod0, member0, org1, mod1, member1 = self._org_vars()

        with_author = Scan.objects.create(author=member0, uploader=mod0,
                pdf="foo", org=org0)
        self.assertEquals(set(Scan.objects.org_filter(mod0)), 
                set([with_author]))

        no_author = Scan.objects.create(uploader=mod0, pdf="foo", org=org0)
        self.assertEquals(set(Scan.objects.org_filter(mod0)), 
                set([with_author, no_author]))

        self.assertEquals(set(Scan.objects.org_filter(mod1)), set())

        # JSON access

        c = self.client
        for u, p in ((mod0.username, "mod"), ("superuser", "superuser")):
            self._json_results(u, p,
                    "/scanning/scans.json",
                    set([with_author.pk, no_author.pk])
            )
        for u, p, status in (
                    (mod0.username, "mod", 200), 
                    ("superuser", "superuser", 200),
                    (mod1.username, "mod", 403),
                ):
            self.client.logout()
            self.client.login(username=u, password=p)
            res = self.client.get("/scanning/scansplits.json/%s" % no_author.pk)
            self.assertEquals(res.status_code, status)
            if status == 200:
                struct = json.loads(res.content)
                self.assertEquals(struct['scan']['id'], no_author.pk)

    def test_mail(self):
        org0, mod0, member0, org1, mod1, member1 = self._org_vars()

        # org0 handles mail for org1
        self.assertEquals(set(Profile.objects.mail_filter(mod0)),
                set([member0.profile, member1.profile]))
        self.assertEquals(set(Profile.objects.mail_filter(mod1)),
                set([member1.profile]))

    def test_search_users(self):
        org0, mod0, member0, org1, mod1, member1 = self._org_vars()
        # Test that the users.json search works for positive and negative
        # queries.
        self._json_results(mod0.username, "mod",
            "/people/users.json?per_page=6&blogger=true&in_org=1&q=memb",
            set([member0.pk]))
        self._json_results(mod0.username, "mod",
            "/people/users.json?per_page=6&blogger=true&in_org=1&q=foo",
            set([]))
        self._json_results(mod0.username, "mod",
            "/people/users.json?per_page=6&blogger=true&in_org=1&q=-memb",
            set([]))
        self._json_results(mod0.username, "mod",
            "/people/users.json?per_page=6&blogger=true&in_org=1&q=-foo",
            set([member0.pk]))

class TestDeleteAccount(BtbLoginTestCase):
    def setUp(self):
        super(TestDeleteAccount, self).setUp()
        self.doc = Document.objects.create(
                author=User.objects.get(username="author"),
                editor=User.objects.get(username="moderator"),
                type="post",
                status="published"
        )
        self.comment = Comment.objects.create(
                document=self.doc,
                user=User.objects.get(username='reader'),
                comment="Hey now",
        )
        self.favorite = Favorite.objects.create(
                document=self.doc,
                user=User.objects.get(username='reader')
        )

    def test_delete_leaving_comments(self):
        u = User.objects.get(username="reader")

        url = reverse("profiles.delete", args=[u.pk])
        self.assertRedirectsToLogin(url)

        self.loginAs("reader")
        res = self.client.get(url)
        self.assertEquals(res.status_code, 200)

        self.client.post(url)
        self._assertUserDeleted(u)

        self.assertEquals(Comment.objects.count(), 1)
        self.assertEquals(Comment.objects.all()[0].user.profile.display_name,
                "(withdrawn)")
        self.assertEquals(Favorite.objects.count(), 1)
        self.assertEquals(Favorite.objects.all()[0].user.profile.display_name,
                "(withdrawn)")


    def _assertUserDeleted(self, u):
        u = User.objects.get(pk=u.pk)
        self.assertEquals(u.username, "withdrawn-%i" % u.pk)
        self.assertFalse(u.is_active)
        self.assertFalse(u.is_staff)
        self.assertFalse(u.is_superuser)
        for prop in ("first_name", "last_name", "password"):
            self.assertEquals(getattr(u, prop), "")
        self.assertEquals(set(u.groups.all()), set([Group.objects.get(name='readers')]))
        for prop in ("blog_name", "mailing_address", "special_mail_handling"):
            self.assertEquals(getattr(u.profile, prop), "")
        self.assertFalse(u.profile.show_adult_content)

    def test_delete_removing_comments(self):
        u = User.objects.get(username='reader')
        url = reverse("profiles.delete", args=[u.pk])
        self.loginAs("reader")
        self.client.post(url, {'delete_comments': 1})
        self._assertUserDeleted(u)

        self.assertEquals(Comment.objects.count(), 0)
        self.assertEquals(Favorite.objects.count(), 0)

class TestOrganizationsJSON(BtbLoginTestCase):
    def _denied(self):
        for method in ("get", "put", "post", "delete"):
            res = getattr(self.client, method)("/people/organizations.json")
            self.assertEquals(res.status_code, 403)
            res = getattr(self.client, method)("/people/affiliations.json")
            self.assertEquals(res.status_code, 403)

    def test_perms(self):
        self._denied()
        self.loginAs("reader")
        self._denied()
        self.loginAs("moderator")
        self._denied()

    def test_get_list(self):
        self.loginAs("admin")
        res = self.client.get("/people/organizations.json")
        self.assertEquals(res.status_code, 200)
        json_res = json.loads(res.content)
        dct = Organization.objects.get().to_dict()
        self.assertEquals(json_res, {
            'results': [dct],
            'pagination': {'count': 1, 'per_page': 12, 'page': 1, 'pages': 1}}
        )

        res = self.client.get("/people/organizations.json?id=1")
        json_res = json.loads(res.content)
        self.assertEquals(json_res, dct)

    def test_put_org(self):
        new_author = User.objects.create(username="newauthor")
        new_author.profile.managed = True
        new_author.profile.blogger = True
        new_author.profile.save()
            
        org = Organization.objects.get()

        self.loginAs("admin")
        org_dict = org.to_dict()
        org_dict['members'].append({'id': new_author.pk})
        res = self.client.put("/people/organizations.json", json.dumps(org_dict))
        self.assertEquals(res.status_code, 200)
        json_res = json.loads(res.content)
        self.assertTrue(new_author.profile.to_dict() in json_res['members'])
        self.assertTrue(new_author in org.members.all())

        # Refresh..
        org_dict = Organization.objects.get(pk=org.pk).to_dict()
        removal = None
        for member in org_dict['members']:
            if member['id'] == new_author.pk:
                removal = member
                break
        self.assertNotEquals(removal, None)
        org_dict['members'].remove(removal)
        res = self.client.put("/people/organizations.json", json.dumps(org_dict))
        self.assertEquals(res.status_code, 200)
        self.assertEquals(json.loads(res.content), org_dict)
        self.assertFalse(new_author in org.members.all())

    def test_post_org(self):
        self.loginAs("admin")
        new_author = User.objects.create(username="newauthor")
        new_author.profile.managed = True
        new_author.profile.blogger = True
        new_author.profile.save()

        res = self.client.post("/people/organizations.json", json.dumps({
            "name": "Second org",
            "slug": "second-org",
            "moderators": [{'id': User.objects.get(username='moderator').pk}],
            "members": [{'id': new_author.pk}],
        }), content_type='application/json')
        self.assertEquals(res.status_code, 200)

        self.assertEquals(Organization.objects.count(), 2)
        org = Organization.objects.get(slug="second-org")
        self.assertEquals(
            set(org.moderators.all()),
            set(User.objects.filter(username='moderator'))
        )
        self.assertEquals(set(org.members.all()), set([new_author]))
        self.assertEquals(org.name, "Second org")
        self.assertEquals(org.slug, "second-org")
        self.assertFalse(org.public)

        # missing arguments
        res = self.client.post("/people/organizations.json", json.dumps({}),
            content_type="application/json")
        self.assertEquals(res.status_code, 400)
        self.assertEquals(json.loads(res.content), {
            "error": "Missing attrs: members, moderators, name, slug"
        })

        # duplicate slug
        res = self.client.post("/people/organizations.json", json.dumps({
            "name": "Third org",
            "slug": "second-org",
            "moderators": [{'id': User.objects.get(username='moderator').pk}],
            "members": [{'id': new_author.pk}],
        }), content_type='application/json')
        self.assertEquals(res.status_code, 400)
        self.assertEquals(json.loads(res.content), {
            "error": "Slug not unique.",
        })

        # multiple memberships: clobber previous membership.
        res = self.client.post("/people/organizations.json", json.dumps({
            "name": "Third org",
            "slug": "third-org",
            "moderators": [{'id': User.objects.get(username='reader').pk}],
            "members": [{'id': new_author.pk}],
        }), content_type='application/json')
        self.assertEquals(res.status_code, 200)
        self.assertEquals(new_author.organization_set.get(),
                Organization.objects.get(slug='third-org'))

        # Make sure moderators group is added....
        self.assertEquals(set(User.objects.get(username='reader').groups.all()),
            set([Group.objects.get(name='readers'), Group.objects.get(name='moderators')]))
        # ... and removed.
        org = Organization.objects.get(slug='third-org')
        org_dict = org.to_dict()
        remove = None
        for mod in org_dict['moderators']:
            if mod['username'] == 'reader':
                remove = mod
                break
        self.assertNotEquals(remove, None)
        org_dict['moderators'].remove(remove)
        res = self.client.put("/people/organizations.json", json.dumps(org_dict))
        self.assertEquals(res.status_code, 200)
        self.assertEquals(
                set(User.objects.get(username='reader').groups.all()),
                set([Group.objects.get(name='readers')])
        )

        #
        # Deletion
        #

        # Delete org
        res = self.client.delete("/people/organizations.json", json.dumps({
            'id': Organization.objects.get(slug='third-org').id
        }), content_type='application/json')
        self.assertEquals(res.status_code, 400)
        self.assertEquals(json.loads(res.content), {
            "error": "Missing parameters: destination_organization",
        })

        # Can't delete default organization
        res = self.client.delete("/people/organizations.json", json.dumps({
            'id': 1
        }), content_type='application/json')
        self.assertEquals(res.status_code, 400)
        self.assertEquals(json.loads(res.content), {
            "error": "Can't delete default organization.",
        })

        # Successful delete.
        res = self.client.delete("/people/organizations.json", json.dumps({
            'id': Organization.objects.get(slug='third-org').pk,
            'destination_organization': Organization.objects.get(slug='second-org').pk,
        }), content_type='application/json')
        self.assertEquals(res.status_code, 200)
        org = Organization.objects.get(slug='second-org')
        self.assertEquals(json.loads(res.content), org.to_dict())

        self.assertEquals(set(Organization.objects.all()), set([
            Organization.objects.get(pk=1), Organization.objects.get(slug='second-org')
        ]))
        self.assertEquals(
            set(new_author.organization_set.all()),
            set([Organization.objects.get(slug='second-org')])
        )
