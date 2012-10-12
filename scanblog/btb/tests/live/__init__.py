from .account_tests import TestAccounts
from .comment_tests import TestComments
from .flag_tests import TestFlags
from .frontend_tests import TestFrontend
from .transcription_tests import TestTranscriptions
from .mod_upload_tests import TestModUploads
from .mod_scan_tests import TestModScans

__all__ = [
    'TestAccounts', 'TestComments', 'TestFlags', 'TestFrontend',
    'TestTranscriptions', 'TestModUploads', 'TestModScans',
]
