# -*- coding: utf-8 -*-
Feature: Process scans
    In order to take scans from raw form to published form
    as a moderator
    I want to process scans into documents.

    Scenario: Upload and process a scan with pending scan.
        Given I am signed in as a moderator for "testorg"
        And there are no scans in the dashboard
        And I enter a pending scan for "Test Author"
        And I upload the scan "ex-post-prof-license.pdf"
        Then I see the split scan interface
        And the "Save" button is disabled
        And the "Edit documents" button is disabled
        Given I set the scan code
        And I mark the pages according to their types
            | page | type    |
            | 1    | ignore  |
            | 2    | post    |
            | 3    | post    |
            | 4    | profile |
            | 5    | profile |
            | 6    | license |
            | 7    | license |
        And I follow the span "Save"
        Then documents for each part are created
            | document | pages |
            | post     | 2     |
            | profile  | 2     |
            | license  | 2     |
        And the "Save" button is disabled
        And the "Edit documents" button is enabled

    Scenario: Edit the documents
        Given I follow the span beginning "Edit documents"
        Then I see the document editing form with 3 documents
        Given I enter the following into document 1
            | Title:     | Tags:                         | Status:   |
            | My Nature  | prison life, inmate rights,   | published |
        And I click "Save" for document 1
        Then document 1 is not saved and published
        And I see an error
        Given I select a highlight on the first page of document 1
        And I click "Save" for document 1
        Then document 1 is saved and published
        Given I enter the following into document 2
            | Status:   |
            | published |
        And I click "Save" for document 2
        Then document 2 is saved and published
        Given I access the url "/blogs/"
        Then I see a post with the title "My Nature"
