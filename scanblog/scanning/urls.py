from django.conf.urls import *

from scanning.views import PendingScans, Scans, Documents, ScanSplits, ScanCodes

scan_id     = '(?P<scan_id>\d+)'
user_id     = '(?P<user_id>\d+)'
document_id = '(?P<document_id>\d+)'

urlpatterns = patterns('scanning.views', 
    (r'^pendingscans.json(/(?P<obj_id>\d+))?$', PendingScans.as_view()),
    (r'^scancodes.json$', ScanCodes.as_view()),
    (r'^scans.json(/(?P<obj_id>\d+))?$', Scans.as_view()),
    (r'^documents.json(/(?P<obj_id>\d+))?$', Documents.as_view()),
    (r'^scansplits.json/(?P<obj_id>\d+)$', ScanSplits.as_view()),
    url(r'^add$', 'scan_add', name='scanning.scan_add'),
    url(r'^replace/{0}?$'.format(scan_id), 'scan_replace', name='scanning.scan_replace'),
    url(r'^delete/{0}?$'.format(scan_id), 'scan_delete', name='scanning.scan_delete'),
    url(r'^reimport/{0}?$'.format(scan_id), 'scan_reimport', name='scanning.scan_reimport'),
    url(r'^merge/{0}?$'.format(scan_id), 'scan_merge', name='scanning.scan_merge'),
    url(r'^delete_doc/{0}?$'.format(document_id), 'doc_delete', name='scanning.delete_doc'),
    url(r'^flag/{0}?$'.format(document_id), 'flag_document', name='scanning.flag_document'),
    url(r'^recent$', 'recent_scans', name='scanning.recent_scans'),

    url(r'^transcribe/{0}$'.format(document_id), 'transcribe_document', name='scanning.transcribe_document'),
    url(r'^transcribe/{0}/list$'.format(document_id), 'revision_list', name='scanning.revision_list'), 
    url(r'^transcribe/{0}/compare$'.format(document_id), 'revision_compare', name='scanning.revision_compare'), 
    url(r'^transcribe/{0}/comment$'.format(document_id), 
        'after_transcribe_comment', name='scanning.after_transcribe_comment'),
)
