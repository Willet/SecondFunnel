Feature: Account functionality
    In order to access the application
    As a customer
    I want to be able to access my account

    Scenario: Login
        Given I visit the "login" page
        And I fill in "username" with "nterwoord"
        And I fill in "password" with "asdf"
        When I press "login"
        Then I see the "store admin" page

    Scenario: Failed Login
        Given I visit the "login" page
        And I fill in "username" with "nterwoord"
        And I fill in "password" with "asdfghjkl"
        When I press "login"
        Then I see the "login" page
        And I see "Your username and password didn't match"

    Scenario: Logout
        Given I login with username "nterwoord" and password "asdf"
        When I click "Logout"
        Then I see the "login" page

    Scenario: Successful password recovery
        Given I visit the "login" page
        And I click "Forgot your password?"
        And I fill in "email" with "nick@willetinc.com"
        And I press "Send Reset Url"
        And I receive an email titled "Pinpoint admin password reset"
        And I visit the link in the email
        And I fill in "new_password1" with "asdfghjkl"
        And I fill in "new_password2" with "asdfghjkl"
        And I press "Change my password"
        And I visit the "login" page
        And I fill in "username" with "nterwoord"
        And I fill in "password" with "asdfghjkl"
        When I press "login"
        Then I see the "store admin" page

    Scenario: Failed password recovery - bad email
        Given I visit the "login" page
        And I click "Forgot your password?"
        And I fill in "email" with "customer@example.com"
        And I press "Send Reset Url"
        Then I see "That e-mail address doesn't have an associated user account"