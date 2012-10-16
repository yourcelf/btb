from .account_tests import TestAccounts
from .comment_tests import TestComments
from .flag_tests import TestFlags
from .frontend_tests import TestFrontend
from .transcription_tests import TestTranscriptions
from .post_from_web_tests import TestPostFromWeb
from .mod_upload_tests import TestModUploads
from .mod_scan_tests import TestModScans
from .mod_users_tests import TestModUsers
from .mod_incoming_tests import TestModIncoming

__all__ = [
    'TestAccounts', 'TestComments', 'TestFlags', 'TestFrontend',
    'TestTranscriptions', 'TestPostFromWeb', 
    'TestModUploads', 'TestModScans', 'TestModUsers', 'TestModIncoming',
]
