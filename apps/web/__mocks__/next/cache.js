// Mock for next/cache in jest environment
// next/cache is a server-only API (uses Node.js internals) that cannot run in jsdom.
module.exports = {
  revalidatePath: jest.fn(),
  revalidateTag: jest.fn(),
  unstable_cache: jest.fn((fn) => fn),
  unstable_noStore: jest.fn(),
};
