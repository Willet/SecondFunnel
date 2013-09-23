/*global jasmine*/
var jasmineEnv = jasmine.getEnv(),
    reporter = new jasmine.ConsoleReporter();

jasmineEnv.addReporter(reporter);
jasmineEnv.execute();