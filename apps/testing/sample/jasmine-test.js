describe("A suite", function() {
    it("contains spec with an expection", function() {
        expect(true).toBe(true);
    });
    
    it("contains spec with numerical expection", function() {
        expect(2).toBe(2);
    });

    it("contains spec that will fail", function() {
        expect(3).toBe(2);
    });
});