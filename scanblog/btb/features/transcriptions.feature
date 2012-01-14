Feature: Leave transcriptions for posts
    In order to improve accessibility of scans
    As a visitor to the site
    I can edit transcriptions
    Scenario: Try to leave a transcription without logging in
        Given I am not signed in
        And I click a transcription link
        Then I am redirected to login

    Scenario: Leave a transcription
        Given I am signed in
        And I click a transcription link
        And I put "This is a transcription" in the transcription form
        And I uncheck the "complete" checkbox
        And I click the button "Save"
        Then I am redirected to the post page
        And the transcription text reads "This is a transcription"
        And the transcription button reads "✍ Partially transcribed"

    Scenario: Complete a transcription
        Given I am signed in
        And I click a transcription link
        And I check the "complete" checkbox
        And I put "Woot unicode transcription ✍" in the transcription form
        And I click the button "Save"
        Then I am redirected to the post page
        And the transcription text reads "Woot unicode transcription ✍"
        And the transcription button reads "✍ Transcribed"

        Then I follow "revisions"
        And I see a revision table
