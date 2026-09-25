const assert = require('node:assert/strict');

global.window = global;
global.document = { addEventListener() {} };

const { countRowsWithLatestPbjData } = require('../Assets/nursing-home-statewide-staffing-comparison.js');
const currentFacilityRows = Array.from({ length: 196 }, (_, index) => ({
  missing_latest_pbj_row: index >= 190
}));

assert.equal(currentFacilityRows.length, 196);
assert.equal(countRowsWithLatestPbjData(currentFacilityRows), 190);
assert.equal(currentFacilityRows.filter(row => row.missing_latest_pbj_row).length, 6);
process.stdout.write('PASS: 196 current facilities, 190 with latest PBJ, 6 without.\n');
