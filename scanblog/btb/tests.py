from django.test import TestCase, TransactionTestCase
from django.conf import settings
from django.contrib.auth.models import User, Group

# TODO this backports the with self.settings construct in the development
# versions of Django. When it becomes standard, we don't need this anymore.
# see http://docs.djangoproject.com/en/dev/topics/testing/#overriding-settings
class BtbWithSettings:
    def __init__(self, hash):
        self.hash = hash
    def __enter__(self):
        self.save = {}
        self.delete = {}
        for key, value in self.hash.iteritems():
            try:
                self.save[key] = getattr(settings, key)
            except AttributeError:
                self.delete[key] = True
            setattr(settings, key, value)
    def __exit__(self, type, value, traceback):
        for key, value in self.save.iteritems():
            setattr(settings, key, value)
        for key, value in self.delete.iteritems():
            delattr(settings, key)

class BtbBaseTestCase():
    # see WithSettings
    def settings(self, *args, **kwargs):
        return BtbWithSettings(kwargs)

    def loginAs(self, name):
        self.assertTrue(self.client.login(username=name, password=name))

class BtbTestCase(TestCase, BtbBaseTestCase):
    pass

class BtbTransactionTestCase(TransactionTestCase, BtbBaseTestCase):
    pass

class BtbLoginTestCase(BtbTestCase):
    fixtures = ['initial_data.json']
    def setUp(self):
        test_users = [{
            'username': 'admin',
            'groups': [],
        }, {
            'username': 'moderator',
            'groups': ['moderators', 'readers'],
        }, {
            'username': 'reader',
            'groups': ['readers'],
        }, {
            'username': 'author',
            'groups': ['authors', 'readers'],
        }]
        for struct in test_users:
            user = User.objects.create(username=struct['username'],
                    is_superuser = struct.get('is_superuser', False))
            user.set_password(user.username)
            user.save()
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

