python /opt/btb/scanblog/manage.py celeryd_detach:
  cmd.run:
    - user: vagrant

nohup python /opt/btb/scanblog/manage.py runserver 0.0.0.0:8000 &:
  cmd.run:
    - user: vagrant

