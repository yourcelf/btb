
get source:
  git.latest:
    - name : https://github.com/yourcelf/btb
    - target: /opt/btb

python-pip:
  pkg.installed

install pyPDF from external:
  pip.installed:
    - name: http://pybrary.net/pyPdf/pyPdf-1.13.tar.gz
    - require:
      - pkg: python-pip

install requirements:
  pip.installed:
    - requirements: /opt/btb/scanblog/requirements.txt
    - require:
      - pkg: python-pip

/opt/btb/scanblog/site_static/CACHE:
  file.directory:
    - makedirs: True
    - user: vagrant

img symbolic link:
  file.symlink:
    - target : /opt/btb/scanblog/static/img
    - name : /opt/btb/scanblog/site_static/CACHE/img

fonts symbolic link:
  file.symlink:
    - target : /opt/btb/scanblog/static/fonts
    - name : /opt/btb/scanblog/site_static/CACHE/fonts
