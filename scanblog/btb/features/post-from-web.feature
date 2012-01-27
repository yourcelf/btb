Feature: Blog from the web
    In order to improve continuity and communication
    As a blogger with computer access
    I can post from the web

    Scenario: Compose a post
        Given I am signed in as an unmanaged blogger
        And I visit the post editor
        And I create a post with status "Publish"
        Then the post appears on my blog

        Given I visit the post editor
        And I create a post with status "Draft"
        Then the post does not appear on my blog
        But I see the post in the post manager

    Scenario: See posts in manager
        Given I am signed in as an unmanaged blogger
        And I visit the post manager
        Then I see a list of posts

        Given I click on the first one
        Then I see the post in the editing form
