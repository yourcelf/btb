
python /opt/btb/scanblog/manage.py syncdb --noinput:
  cmd.run:
    - user: vagrant
    - unless: ls /opt/btb//scanblog/deploy/dev.db

python /opt/btb/scanblog/manage.py migrate && touch /opt/btb/scanblog/deploy/migrate_done:
  cmd.run:
    - user: vagrant
    - unless: ls /opt/btb/scanblog/deploy/migrate_done

python /opt/btb/scanblog/manage.py loaddata btb/fixtures/initial_data.json && touch /opt/btb/scanblog/deploy/loaddata_done:
  cmd.run:
    - user: vagrant
    - unless: ls /opt/btb/scanblog/deploy/loaddata_done

/tmp/create_admin.py:
  file.managed:
    - user: vagrant
    - source: salt://create_admin.py

python /opt/btb/scanblog/manage.py shell << /tmp/create_admin.py && touch /opt/btb/scanblog/deploy/admin_done:
  cmd.run:
    - user: vagrant
    - require: 
      - file : /tmp/create_admin.py
    - unless: ls /opt/btb/scanblog/deploy/admin_done
