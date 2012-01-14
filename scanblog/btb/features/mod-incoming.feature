Feature: Incoming mail
    In order to maintain high quality of service
    As a mail receiver for Between the Bars
    I want to log letters I have received.

    Scenario: Enter a new letter
        Given I am signed in as a moderator for "testorg"
        And I access the url "/moderation/"
        And I follow "Incoming mail"
        Then I see the incoming mail form
        Given I type "te" in the user search form
        Then I see choices for users
        Given I click the first user choice
        Then a pendingscan entry for that choice is created
        And I see that user choice in the pending list

    Scenario: Mark a choice missing
        Given I click the missing checkbox
        Then the pendingscan entry is marked missing
        Given I follow the span "Missing"
        Then I see that user choice in the pending list
        And I see the choice under the missing list in the user detail page

    Scenario: Delete a choice
        Given I delete the first missing choice
        Then the choice disappears
