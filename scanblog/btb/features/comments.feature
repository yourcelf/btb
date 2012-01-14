Feature: Leave comments
    In order to communicate with people in prison
    As a visitor to the site
    I can leave replies

    Scenario: Comment while not signed in
        Given post 5 has no comments
        And I am not signed in
        And I go to post 5
        And I put "My comment" in the comment form
        And I click the submit button
        Then I am redirected to login
        And I login as "testuser:testuser"
        And I see a full post
        And I see the comment "My comment"

    # Signed in from here on down.

    Scenario: Comment while signed in
        Given I am signed in
        And I go to post 5
        And I put "My second comment" in the comment form
        And I click the submit button
        Then I see a full post
        And I see the comment "My second comment"

    Scenario: Edit my comment
        Given I go to post 5
        And I edit the comment "My second comment"
        Then I see the edit form
        And I put "My second comment edit" in the edit form
        And I click the submit button

        Then I see a full post
        And I see the comment "My second comment edit"
        And I don't see the comment "My second comment"

    Scenario: Delete my comment
        Given I go to post 5
        And I delete the comment "My second comment edit"
        Then I see the delete confirmation
        And I click the submit button

        Then I see a full post
        And I don't see the comment "My second comment edit"

    Scenario: Cleanup
        Given post 5 has no comments
