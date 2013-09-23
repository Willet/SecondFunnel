/*global jasmine*/
var jasmineEnv = jasmine.getEnv(),
    reporter = new jasmine.HtmlReporter();

jasmineEnv.updateInterval = 250;

jasmineEnv.specFilter = function(spec) {
    return reporter.specFilter(spec);
};

jasmineEnv.addReporter(reporter);
jasmineEnv.execute();