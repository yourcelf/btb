curl -L https://wkhtmltopdf.googlecode.com/files/wkhtmltopdf-0.11.0_rc1-static-{{ grains['arch'] }}.tar.bz2 | tar xjv > wkhtmltopdf
sudo mv wkhtmltopdf /usr/local/bin
sudo gem install compass
sudo npm install -g coffee-script
