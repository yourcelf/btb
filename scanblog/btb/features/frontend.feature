Feature: Pages display correctly
    Scenario: Access the blogs page
        Given I access the url "/"
        And I follow "Blogs"
        Then I see the header "Recent posts from all authors"
        And I see a page of post snippets

    Scenario: Access a post
        Given I access the url "/"
        And I follow "Blogs"
        And I follow "Reply"
        Then I see a full post
        And I see a reply form

    Scenario: Access the people page
        Given I access the url "/"
        And I follow "People"
        Then I see the header "All authors"
        And I see a list of people

    Scenario: Access an author's posts
        Given I access the url "/people/"
          And I follow a person link
        Then I see a header
         And I see some post snippets

    Scenario: Access about pages
        Given I access the url "/"
        And I follow "About"
        Then I see the subnav links
            | link text                     |
            | Community Guidelines          |
            | Frequently Asked Questions    |
            | News                          |
            | Mailing list                  |

    Scenario: Expected URLs work
        Then the following links work
            | url                   |
            | /                     |
            | /blogs/               |
            | /people/              |
            | /about/               |
            | /about/guidelines/    |
            | /about/faq/           |
            | /about/join/          |
            | /accounts/login/      |
            | /accounts/register/   |
