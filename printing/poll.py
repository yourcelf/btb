import sys
import click2mail
from utils import parser

parser.add_argument('batch_id', type=int)
args = parser.parse_args()
c2m = click2mail.Click2MailBatch(args.username, args.password, None, None)
c2m.batch_id = args.batch_id
c2m.poll_job_complete()

