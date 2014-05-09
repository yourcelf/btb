install dependencies:
  pkg.installed:
    - refresh: True
    - pkgs:
      - git 
      - mercurial 
      - poppler-utils 
      - pdftk 
      - imagemagick 
      - rubber 
      - rabbitmq-server 
      - python-dev 
      - postgresql-server-dev-all 
      - nodejs 
      - npm 
      - texlive-fonts-extra 
      - texlive-fonts-recommended 
      - texlive-font-utils 
      - texlive-generic-recommended 
      - texlive-latex-extra 
      - texlive-latex-recommended 
      {% if grains['oscodename'] == 'trusty' %}
      - fonts-sil-gentium
      - ruby
      - nodejs-legacy
      {% else %}
      - ttf-sil-gentium
      - rubygems 
      {% endif %}

install from source:
  cmd.script:
    - name: /tmp/install_deps_from_src.sh
    - source: salt://install_deps_from_src.sh 

