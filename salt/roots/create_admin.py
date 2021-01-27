from sh import *
u = User.objects.create(username='admin', is_superuser=True, is_staff=True)
u.set_password('admin')
u.save()
exit()
