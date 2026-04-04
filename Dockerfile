FROM python:2.7.18-buster AS dev
COPY --from=ghcr.io/astral-sh/uv:0.8.0 /uv /uvx /bin/

# Use the Debian archive for EOL Buster
RUN echo "deb http://archive.debian.org/debian/ buster main" > /etc/apt/sources.list \
  && echo "deb http://archive.debian.org/debian-security/ buster/updates main" >> /etc/apt/sources.list \
  && echo "deb http://archive.debian.org/debian/ buster-updates main" >> /etc/apt/sources.list

# dev user
ARG UID=1000
ARG GID=1000
RUN groupadd -g "${GID}" dev \
  && useradd --create-home --no-log-init -u "${UID}" -g "${GID}" dev

# system dependencies
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
  && apt-get install -y ca-certificates ca-certificates-java \
  && update-ca-certificates --fresh \
  && apt-get install -y \
      antiword \
      build-essential \
      curl \
      fonts-sil-gentium \
      ghostscript \
      git \
      imagemagick \
      libssl-dev \
      mercurial \
      nodejs \
      npm \
      pdftk \
      poppler-utils \
      postgresql-client \
      python-dev \
      rabbitmq-server \
      rubber \
      ruby-dev \
      rubygems \
      texlive-font-utils \
      texlive-fonts-extra \
      texlive-fonts-recommended \
      texlive-generic-recommended \
      texlive-latex-extra \
      texlive-latex-recommended \
      xfonts-base \
      xfonts-75dpi \
  && rm -rf /var/lib/apt/lists/*

RUN curl -L https://ctan.org/tex-archive/obsolete/fonts/gentium/fonts/truetype/public/gentium?lang=en -o /usr/share/fonts/truetype/gentium/GenR102.ttf

# Python deps
RUN mkdir -p /opt/app
RUN chown dev:dev /opt/app
WORKDIR /opt/app
COPY --chown=dev:dev pyproject.toml uv.loc[k] shrinkwrap.txt ./
# Install deps into system python
#ENV UV_PROJECT_ENVIRONMENT=/usr/local
#RUN uv sync 
RUN pip install -r shrinkwrap.txt
RUN pip install psycopg2-binary

# additional weird deps
RUN gem install rubygems-update -v 3.3.26 --no-document \
  && update_rubygems \
  && gem install compass --no-document
RUN npm install -g coffee-script
RUN curl -L https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.buster_amd64.deb -o /tmp/wkhtmltox_0.12.6-1.buster_amd64.deb \
  && dpkg -i /tmp/wkhtmltox_0.12.6-1.buster_amd64.deb \
  && rm /tmp/wkhtmltox_0.12.6-1.buster_amd64.deb

## sass
#ARG SASS_VERSION=1.89.2
#ARG SASS_ARCH=x64
#RUN curl -L "https://github.com/sass/dart-sass/releases/download/${SASS_VERSION}/dart-sass-${SASS_VERSION}-linux-${SASS_ARCH}.tar.gz" -o /tmp/sass.tar.gz \
#  && tar -xzf /tmp/sass.tar.gz -C /opt \
#  && ln -s /opt/dart-sass/sass /usr/local/bin/sass

# project
USER dev
WORKDIR /opt/app
COPY . .

CMD ./scanblog/manage.py runserver 0.0.0.0:$PORT

#
# Selenium
#
FROM dev AS selenium
USER root
RUN apt-get update \
  && apt-get install -y \
    firefox-esr \
    xwayland \
    xauth \
    x11-utils \
    dbus \
  && rm -rf /var/lib/apt/lists/*
RUN curl -L https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz -o /tmp/geckodriver-v0.33.0-linux64.tar.gz \
  && tar -xvzf /tmp/geckodriver-v0.33.0-linux64.tar.gz -C /tmp \
  && chmod a+x /tmp/geckodriver \
  && mv /tmp/geckodriver /usr/local/bin/ \
  && rm /tmp/geckodriver-v0.33.0-linux64.tar.gz

USER dev
WORKDIR /opt/app
COPY . .
CMD ./scanblog/manage.py test
