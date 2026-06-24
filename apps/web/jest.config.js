const nextJest = require('next/jest');

const createJestConfig = nextJest({
  dir: './',
});

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
    // Mock Next.js server-only APIs that cannot run in jsdom environment
    '^next/cache$': '<rootDir>/__mocks__/next/cache.js',
    '^next/headers$': '<rootDir>/__mocks__/next/headers.js',
  },
  testPathIgnorePatterns: ['<rootDir>/e2e/'],
};

module.exports = async () => {
  const config = await createJestConfig(customJestConfig)();
  config.transformIgnorePatterns = [
    '/node_modules/(?!(iron-session|uncrypto)/)',
  ];
  return config;
};
