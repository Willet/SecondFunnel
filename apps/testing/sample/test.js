// Test case: GreeterTest
// Test name: testGreet
// GreeterTest.testGreet
GreeterTest = TestCase("GreeterTest");

GreeterTest.prototype.testGreet = function() {
    var greeter = new myapp.Greeter();
    assertEquals("Hello World!", greeter.greet("World"));
};
