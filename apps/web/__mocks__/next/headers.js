// Mock for next/headers in jest environment
// next/headers is a server-only API that cannot run in jsdom.
const mockHeaders = new Map([
  ['x-forwarded-for', '127.0.0.1'],
]);

const headersProxy = {
  get: (key) => mockHeaders.get(key.toLowerCase()) ?? null,
  has: (key) => mockHeaders.has(key.toLowerCase()),
  getAll: () => Array.from(mockHeaders.entries()),
};

module.exports = {
  headers: jest.fn(() => Promise.resolve(headersProxy)),
  cookies: jest.fn(() => Promise.resolve({
    get: jest.fn(() => null),
    set: jest.fn(),
    delete: jest.fn(),
  })),
};
