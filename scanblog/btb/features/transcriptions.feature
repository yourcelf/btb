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
        And I have previously left no comments on that post
        And I click the button "Save"
        Then I am redirected to the after transcribe comment page
        Given I click the submit button
        Then I am redirected to the post page
        And the transcription text reads "This is a transcription"
        And the transcription button reads "✍ Partially transcribed"
        And I see the comment "Thanks for writing! I worked on the transcription for your post."

    Scenario: Complete a transcription
        Given I am signed in
        And I click a transcription link
        And I check the "complete" checkbox
        And I put "Woot unicode transcription ✍" in the transcription form
        And I have previously left comments on that post
        And I click the button "Save"
        # This time, I've left a comment previously, so I go straight to the post page
        Then I am redirected to the post page
        And the transcription text reads "Woot unicode transcription ✍"
        And the transcription button reads "✍ Transcribed"

        Then I follow "revisions"
        And I see a revision table
