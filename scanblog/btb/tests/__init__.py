from django.test import TestCase, TransactionTestCase
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.contrib.sites.models import Site
from django.core import mail

from profiles.models import Organization

from live import *

class BtbBaseTestCase():
    fixtures = ["initial_data.json"]
    def loginAs(self, name):
        self.assertTrue(self.client.login(username=name, password=name))

class BtbTestCase(TestCase, BtbBaseTestCase):
    pass

class BtbMailTestCase(BtbTestCase):
    def setUp(self, *args, **kwargs):
        super(BtbMailTestCase, self).setUp(*args, **kwargs)
        self.user_subject_prefix = "[%s] " % Site.objects.get_current().name
        self.admin_subject_prefix = settings.EMAIL_SUBJECT_PREFIX

    def assertOutboxContains(self, subjects):
        """
        Assert that only the subjects given are in the outbox.
        """
        self.assertEquals(set([m.subject for m in mail.outbox]),
                          set(subjects))

    def assertOutboxIsEmpty(self):
        self.assertEquals(mail.outbox, [])

    def clear_outbox(self):
        for i in range(len(mail.outbox)):
            mail.outbox.pop()

class BtbTransactionTestCase(TransactionTestCase, BtbBaseTestCase):
    pass

class BtbLoginTestCase(BtbTestCase):
    def setUp(self):
        org = Organization.objects.create(name='org')
        test_users = [{
            'username': 'admin',
            'is_superuser': True,
            'managed': False,
            'moderates': org,
            'groups': [],
        }, {
            'username': 'moderator',
            'managed': False,
            'moderates': org,
            'groups': ['moderators', 'readers'],
        }, {
            'username': 'reader',
            'managed': False,
            'groups': ['readers'],
        }, {
            'username': 'author',
            'managed': True,
            'member': org,
            'groups': ['authors', 'readers'],
        }]
        for struct in test_users:
            user = User.objects.create(username=struct['username'],
                    is_superuser = struct.get('is_superuser', False))
            user.set_password(user.username)
            user.save()
            user.profile.managed = struct['managed']
            user.profile.save()
            if struct.get('moderates', None):
                org.moderators.add(user)
            if struct.get('member', None):
                org.members.add(user)
            for group in struct['groups']:
                user.groups.add(Group.objects.get(name=group))

    def assertRedirectsToLogin(self, *args, **kwargs):
        kwargs['follow'] = True
        response = self.client.get(*args, **kwargs)
        self.assertEquals(response.redirect_chain[0],
            ("http://testserver" + settings.LOGIN_URL + "?next=" + args[0], 302)
        )

    def assertStatus200(self, *args, **kwargs):
        kwargs['follow'] = True
        res = self.client.get(*args, **kwargs)
        self.assertEquals(res.redirect_chain, [])
        self.assertEquals(res.status_code, 200)

