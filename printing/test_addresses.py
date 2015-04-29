import os
from click2mail import Click2MailBatch
from utils import parser

jobs = [{
    "startingPage": 1,
    "endingPage": 1,
    "type": "letter",
    "recipients": [{
        "name": "Kyle De Wolf",
        "address1": "14966-052",
        "address2": "Low Security Correctional Institution Allenwood",
        "address3": "PO Box 1000",
        "city": "White Deer",
        "state": "PA",
        "zip": "17887"
    }, {
        "name": "Marcus T. Rogers Jr",
        "address1": "#377571",
        "address2": "John Burke Correctional Center",
        "address3": "P.O. Box 900",
        "city": "Waupun",
        "state": "WI",
        "zip": "53963"
    }, {
        "name": "Craig Middlemass",
        "address1": "#16988-014 Creek B",
        "address2": "Federal Correctional Institution",
        "address3": "P.O. Box 7007",
        "city": "Marianna",
        "state": "FL",
        "zip": "32447-7007"
    }, {
        "name": "Johnny E. Mahaffey",
        "address1": "32363",
        "address2": "Wateree 193",
        "address3": "4460 Broad River Rd.",
        "city": "Columbia",
        "state": "SC",
        "zip": "29210-4012"
    }]
}]

if __name__ == "__main__":
    args = parser.parse_args()
    batch = Click2MailBatch(
        username=args.username,
        password=args.password,
        filename="tests/mailing_dir/letters/frantisek-loukianos-letter10.pdf",
        jobs=jobs,
        staging=True)
    batch.run()
