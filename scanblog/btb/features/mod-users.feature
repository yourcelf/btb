Feature: Writer accounts
    In order to handle incoming mail
    as a moderator
    I want to find and create user accounts.

    Scenario: Search for a non-existent account and create one.
        Given I am signed in as a moderator for "testorg"
        And there is no user named "George Doesnotexist"
        And I search for the user "george doesnotexist"
        Then I see "No results" in the user list
        Given I click the create user link
        Then I see the create user form
        And the name field contains "George Doesnotexist"
        Given I enter an address in the create user form
        And I click the button "Create new user"
        Then a new user named "George Doesnotexist" is created
        # Cleanup
        Then delete the user "George Doesnotexist"

        # Long names
        Given I search for the user "Doesnotexist with a very long name"
        And there is no user named "Doesnotexist With A Very Long Name"
        And I click the create user link
        And I enter an address in the create user form
        And I click the button "Create new user"
        Then a new user named "Doesnotexist With A Very Long Name" is created
        # Cleanup
        Then delete the user "Doesnotexist With A Very Long Name"
