Feature: Account functionality
    In order to access the application
    As a customer
    I want to be able to access my account

    Scenario: Login
        Given I visit the "login" page
        And I fill the field "username" with "customer"
        And I fill the field "password" with "password"
        When I press the "login" button
        Then I see the "store admin" page

    Scenario: Failed Login
        Given I visit the "login" page
        And I fill the field "username" with "customer"
        And I fill the field "password" with "badpassword"
        When I press the "login" button
        Then I see the "login" page
        And I see the text "Your username and password didn't match"

    Scenario: Logout
        Given I have logged in successfully
        When I press the "logout" button
        Then I see the "login" page

    Scenario: Successful password recovery
        Given I visit the "login" page
        And I press the "Forgot your password?" button
        And I fill the "email" field with "customer@example.com"
        And I press the "Send Reset Url" button
        And I receive an email from ""
        And I visit the link in the email
        And I fill in the "password" field with "newpassword"
        And I fill in the "verify" field with "newpassword"
        And I press the "Change my password" button
        And I visit the "login" page
        And I fill the field "username" with "customer"
        And I fill the field "password" with "newpassword"
        When I press the "login" button
        Then I see the "store admin" page

    Scenario: Failed password recovery - bad email
        Given I visit the "login" page
        And I press the "Forgot your password?" button
        And I fill the "email" field with "customer@example.com"
        And I press the "Send Reset Url" button
        Then I see the text "That e-mail address doesn't have an associated user account"