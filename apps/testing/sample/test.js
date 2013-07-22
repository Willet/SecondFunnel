// Test case: GreeterTest
// Test name: testGreet
// GreeterTest.testGreet
TestCase("GreeterTest", {
    testGreet: function() {
        var greeter = new myapp.Greeter();
        assertEquals("Hello World!", greeter.greet("World"));
    }
});
