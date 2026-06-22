require('@testing-library/jest-dom');
const { toHaveNoViolations } = require('jest-axe');
expect.extend(toHaveNoViolations);

const { TextEncoder, TextDecoder } = require('util');
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;


