Feature: uploading of scans
    In order to have scans on the site
    as a moderator
    I want to be able to upload them.

    Scenario: upload files
        Given I am signed in as a moderator for "testorg"
        And there are no scans in the dashboard
        And I access the url "/"
        And I follow "Upload"
        Then I see the upload form
        And I can upload the following files successfully
            | filename                 | number of scans |
            | unixzip.zip              | 2               |
            | maczip.zip               | 2               |
            | ex-req-post-photo.pdf    | 1               |
