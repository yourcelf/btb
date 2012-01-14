Feature: flagging content
    In order to maintain high content quality
    As a visitor to Between the Bars
    I want to be able to flag content that is problematic.

    Scenario: Flag a post
        Given I am not signed in
        And document 5 has no flags
        And I access the url "/posts/5"
        And I click the flag button
        Then I am redirected to login
        Given I login as "testuser:testuser"
        Then I see the flag form
        Given I enter "This post has problems" in the flag form
        And I click the submit button
        Then I see a flag confirmation
        Given document 5 has no flags

    Scenario: Flag a comment
        Given document 2 has a comment and no flags
        And I am signed in
        And I access the url "/posts/2"
        And I click the comment flag button
        Then I see the flag form
        Given I enter "This post has problems" in the flag form
        And I click the submit button
        Then I see a flag confirmation
        Given document 2 has a comment and no flags

