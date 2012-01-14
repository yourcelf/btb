Feature: User accounts
    In order to have identities that persist
    As a visitor to the site
    I want to have a user account

    Scenario: Sign in and basic UI
        Given I am not signed in
        And I access the url "/"
        Then I see links to "Sign in" and "Join"
        And I follow "Sign in"
        And I see the login form
        And I see the registration form
        And I login as "testuser:testuser"
        And I am redirected to "/"
        And I see "testuser" in the auth section
    
    Scenario: Register
        Then the following registrations work
            | username  | email     | password1 | password2 | delete    |
            | testuser1 | t@a.com   | testuser1 | testuser1 | yes       |
            | testuser1 |           | testuser1 | testuser1 | yes       |
        And the following registrations don't work
            | username  | email     | password1 | password2 | delete    |
            | uploader  |           | pass      | pass      | no        |
            | testuser1 |           | doesnt    | match     | yes       |

    Scenario: Delete my account, but leave comments.
        Given I am a user named "testuser1" with comments
        And I delete my account
        Then the account "testuser1" is made inactive
        And the comments by "testuser1" remain
        And the display name for "testuser1" is "(withdrawn)"
        Then delete the working user

    Scenario: Delete my account, and delete comments.
        Given I am a user named "testuser1" with comments
        And I delete my account and comments
        Then the account "testuser1" is made inactive
        And the comments by "testuser1" are deleted
        Then delete the working user
