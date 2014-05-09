from django.conf.urls import *

from correspondence.views import CorrespondenceList, Letters, Mailings, \
    NeededLetters, StockResponses

letter_id = "(?P<letter_id>\d+)"
mailing_id = "(?P<mailing_id>\d+)"
user_id = "(?P<user_id>\d+)"
comment_id = "(?P<comment_id>\d+)"


urlpatterns = patterns('correspondence.views',
    url(r'^correspondence.json(/{0})?$'.format(user_id), CorrespondenceList.as_view()),
    url(r'^letters.json(/{0})?'.format(letter_id), Letters.as_view()),
    url(r'^mailings.json(/{0})?'.format(mailing_id), Mailings.as_view()),
    url(r'^needed_letters.json', NeededLetters.as_view()),
    url(r'^stock_responses.json', StockResponses.as_view()),
    url(r'^mass_mailing_spreadsheet/(?P<who>.*)', 'mass_mailing_spreadsheet',
        name='correspondence.mass_mailing_spreadsheet'),
    url(r'^envelope/{0}?(/(?P<reverse>return))?$'.format(user_id), 'print_envelope', 
        name='correspondence.print_envelope'),
    url(r'^letter/{0}?$'.format(letter_id), 'show_letter', 
        name='correspondence.show_letter'),
    url(r'^comments/{0}$'.format(letter_id), 'recent_comments_letter', 
        name='correspondence.recent_comments_letter'),
    url(r'^preview_letter/$', 'preview_letter', 
        name='correspondence.preview_letter'),
    url(r'^comment_removal_letter_preview_frame/{0}$'.format(comment_id),
        'comment_removal_letter_preview_frame', 
        name='correspondence.comment_removal_letter_preview_frame'),
    url(r'^collate_mailing/{0}?$'.format(mailing_id), 'get_mailing_file', 
        name='correspondence.collate_mailing'),
    url(r'^clear_cache/{0}?$'.format(mailing_id), 'clear_mailing_cache',
        name='correspondence.clear_mailing_cache'),
    url(r'^mailing_labels/$', 'mailing_label_sheet', name='correspondence.mailing_labels'),
    url(r'^envelopes/$', 'print_envelopes', name='correspondence.envelopes'),
)
