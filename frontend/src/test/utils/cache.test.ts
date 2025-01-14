import { describe, it, expect, vi, beforeEach } from 'vitest';
import { Cache } from '$lib/utils/cache';

describe('Cache', () => {
    describe('string cache', () => {
        let cache: Cache<string>;

        beforeEach(() => {
            vi.useFakeTimers();
            cache = new Cache(1000); // 1 second TTL for testing
        });

        it('should store and retrieve values', () => {
            cache.set('key1', 'value1');
            expect(cache.get('key1')).toBe('value1');
        });

        it('should return undefined for non-existent keys', () => {
            expect(cache.get('non-existent')).toBeUndefined();
        });

        it('should expire entries after TTL', () => {
            cache.set('key1', 'value1');
            expect(cache.get('key1')).toBe('value1');

            vi.advanceTimersByTime(1001); // Just past TTL
            expect(cache.get('key1')).toBeUndefined();
        });

        it('should clear all entries', () => {
            cache.set('key1', 'value1');
            cache.set('key2', 'value2');
            expect(cache.size).toBe(2);

            cache.clear();
            expect(cache.size).toBe(0);
            expect(cache.get('key1')).toBeUndefined();
            expect(cache.get('key2')).toBeUndefined();
        });

        it('should cleanup expired entries', () => {
            cache.set('key1', 'value1');
            cache.set('key2', 'value2');
            expect(cache.size).toBe(2);

            vi.advanceTimersByTime(1001); // Just past TTL
            cache.cleanup();
            expect(cache.size).toBe(0);
        });

        it('should keep unexpired entries during cleanup', () => {
            cache.set('key1', 'value1');
            vi.advanceTimersByTime(500); // Half TTL
            cache.set('key2', 'value2');

            vi.advanceTimersByTime(501); // Just past TTL for key1
            cache.cleanup();

            expect(cache.size).toBe(1);
            expect(cache.get('key1')).toBeUndefined();
            expect(cache.get('key2')).toBe('value2');
        });

        it('should use default TTL if not specified', () => {
            const defaultCache = new Cache<string>();
            defaultCache.set('key1', 'value1');

            vi.advanceTimersByTime(5 * 60 * 1000 - 1); // Just before default TTL
            expect(defaultCache.get('key1')).toBe('value1');

            vi.advanceTimersByTime(1); // Just past default TTL
            expect(defaultCache.get('key1')).toBeUndefined();
        });

        it('should update timestamp when setting existing key', () => {
            cache.set('key1', 'value1');
            vi.advanceTimersByTime(500); // Half TTL

            cache.set('key1', 'value2'); // Update value and timestamp
            vi.advanceTimersByTime(501); // Just past original TTL

            expect(cache.get('key1')).toBe('value2'); // Should still be valid
        });
    });

    describe('object cache', () => {
        interface TestObject {
            id: number;
            name: string;
            nested: { value: boolean };
        }

        let cache: Cache<TestObject>;

        beforeEach(() => {
            vi.useFakeTimers();
            cache = new Cache(1000);
        });

        it('should handle complex objects', () => {
            const obj: TestObject = {
                id: 1,
                name: 'test',
                nested: { value: true }
            };

            cache.set('obj', obj);
            const retrieved = cache.get('obj');

            expect(retrieved).toEqual(obj);
            expect(retrieved?.nested.value).toBe(true);
        });
    });

    describe('array cache', () => {
        interface ValueObject {
            value: number;
        }

        type TestArray = Array<number | ValueObject>;
        let cache: Cache<TestArray>;

        function isValueObject(item: number | ValueObject): item is ValueObject {
            return typeof item === 'object' && item !== null && 'value' in item;
        }

        beforeEach(() => {
            vi.useFakeTimers();
            cache = new Cache(1000);
        });

        it('should handle arrays', () => {
            const arr: TestArray = [1, 2, { value: 3 }];
            cache.set('arr', arr);
            const retrieved = cache.get('arr');

            expect(retrieved).toEqual(arr);
            const lastItem = retrieved?.[2];
            if (lastItem && isValueObject(lastItem)) {
                expect(lastItem.value).toBe(3);
            } else {
                throw new Error('Expected last item to be a ValueObject');
            }
        });
    });

    describe('nullable cache', () => {
        let cache: Cache<string | null | undefined>;

        beforeEach(() => {
            vi.useFakeTimers();
            cache = new Cache(1000);
        });

        it('should handle null and undefined values', () => {
            cache.set('null', null);
            cache.set('undefined', undefined);

            expect(cache.get('null')).toBeNull();
            expect(cache.get('undefined')).toBeUndefined();
        });
    });
});
