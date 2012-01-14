.. highlight:: bash

Customizing
===========

If you are going to run your own instance of Between the Bars, great!  But
there are several things you should change first.

Site name
---------

Templates all over the site refer to `{{ site.name }}` -- on our site, that's "Between the Bars".  Set your site's name using the admin interface.

1. Log in as a superuser or staff user
2. Navigate to ``/admin/sites/site/``
3. Change the domain and display name to suitable values.

Return address
---------------
Change the default organizational contact and mailing address.

1. Log in as a superuser or staff user
2. Navigate to ``/admin/profiles/organization/``
3. Change the name, mailing address, and personal contact of the organization.

Templates and branding
----------------------

The following templates contain Between the Bars branding and should be modified to suit your organization.  Please fix anything that would create confusion for users:
 * ``scanblog/templates/site_base.html``: change the contact address.
 * Everything in ``scanblog/templates/about/``, particularly:

   * ``index.html``: replace with your own "about" info.
   * ``dmca.html``: put your own DMCA contact info in
   * ``terms.html``: put terms for your organization, referencing your name
   * ``privacy.html``: put a policy for your organization, referencing your name and URL
   * ``faq.html``: change authorship, contact address, and other details
   * ``guidelines.html``: change contact address.
 * ``scanblog/templates/home.html``: Remove/change quotes and names to suit your organization.  Make yer home page pretty.
 * ``scanblog/tempaltes/500.html``: put your own URL in.
 * Change logos referenced in:

   * ``scanblog/templates/site_base.html``
   * ``scanblog/templates/home.html``

Terms to grep for in the templates include::

    grep -Ri between scanblog/templates/
    grep -Ri detar scanblog/templates/
    grep -Ri civic scanblog/templates/
    grep -Ri '\bmit\b' scanblog/templates/

