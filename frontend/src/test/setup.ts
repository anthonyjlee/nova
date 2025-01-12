import '@testing-library/jest-dom';
import { vi, expect } from 'vitest';
import { fetch } from 'cross-fetch';

// Extend Vitest matchers
declare module 'vitest' {
    interface Assertion {
        toHaveBeenCalledOnceWith: (...args: unknown[]) => boolean;
    }
}

// Mock fetch globally
global.fetch = fetch;

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
}));

// Add custom matchers
expect.extend({
    toHaveBeenCalledOnceWith(received: unknown, ...args: unknown[]) {
        if (typeof received !== 'object' || received === null || !('mock' in received)) {
            return {
                pass: false,
                message: () => `expected ${received} to be a mock function`,
            };
        }

        const mockFn = received as { mock: { calls: unknown[][] }; getMockName: () => string };
        const pass = mockFn.mock.calls.length === 1 &&
            JSON.stringify(mockFn.mock.calls[0]) === JSON.stringify(args);

        return {
            pass,
            message: () =>
                `expected ${mockFn.getMockName()} to have been called once with ${JSON.stringify(args)}`,
        };
    },
});
