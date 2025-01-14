import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { debounce } from '$lib/utils/debounce';

describe('debounce', () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it('should delay function execution', async () => {
        const func = vi.fn().mockReturnValue('result');
        const debouncedFunc = debounce(func, 100);

        const promise = debouncedFunc();
        expect(func).not.toHaveBeenCalled();

        vi.advanceTimersByTime(50);
        expect(func).not.toHaveBeenCalled();

        vi.advanceTimersByTime(50);
        expect(func).toHaveBeenCalledTimes(1);

        const result = await promise;
        expect(result).toBe('result');
    });

    it('should only execute once for multiple calls within wait period', async () => {
        const func = vi.fn().mockReturnValue('result');
        const debouncedFunc = debounce(func, 100);

        const promise1 = debouncedFunc();
        const promise2 = debouncedFunc();
        const promise3 = debouncedFunc();

        vi.advanceTimersByTime(99);
        expect(func).not.toHaveBeenCalled();

        vi.advanceTimersByTime(1);
        expect(func).toHaveBeenCalledTimes(1);

        const [result1, result2, result3] = await Promise.all([promise1, promise2, promise3]);
        expect(result1).toBe('result');
        expect(result2).toBe('result');
        expect(result3).toBe('result');
    });

    it('should use latest arguments for delayed execution', async () => {
        const func = vi.fn().mockImplementation((arg: string) => arg);
        const debouncedFunc = debounce(func, 100);

        const promise1 = debouncedFunc('first');
        const promise2 = debouncedFunc('second');
        const promise3 = debouncedFunc('third');

        vi.advanceTimersByTime(100);
        expect(func).toHaveBeenCalledWith('third');

        const [result1, result2, result3] = await Promise.all([promise1, promise2, promise3]);
        expect(result1).toBe('third');
        expect(result2).toBe('third');
        expect(result3).toBe('third');
    });

    it('should handle async functions', async () => {
        const asyncFunc = vi.fn().mockResolvedValue('async result');
        const debouncedFunc = debounce(asyncFunc, 100);

        const promise = debouncedFunc();
        expect(asyncFunc).not.toHaveBeenCalled();

        vi.advanceTimersByTime(100);
        expect(asyncFunc).toHaveBeenCalledTimes(1);

        const result = await promise;
        expect(result).toBe('async result');
    });

    it('should handle async function rejections', async () => {
        const error = new Error('Async error');
        const asyncFunc = vi.fn().mockRejectedValue(error);
        const debouncedFunc = debounce(asyncFunc, 100);

        const promise = debouncedFunc();
        vi.advanceTimersByTime(100);

        await expect(promise).rejects.toThrow(error);
    });

    it('should reject all pending promises on error', async () => {
        const error = new Error('Test error');
        const func = vi.fn().mockRejectedValue(error);
        const debouncedFunc = debounce(func, 100);

        const promise1 = debouncedFunc();
        const promise2 = debouncedFunc();
        const promise3 = debouncedFunc();

        vi.advanceTimersByTime(100);

        await expect(Promise.all([promise1, promise2, promise3])).rejects.toThrow(error);
    });

    it('should reset timer on each call', async () => {
        const func = vi.fn().mockReturnValue('result');
        const debouncedFunc = debounce(func, 100);

        const promise1 = debouncedFunc();
        vi.advanceTimersByTime(50);

        const promise2 = debouncedFunc();
        vi.advanceTimersByTime(50);
        expect(func).not.toHaveBeenCalled();

        vi.advanceTimersByTime(50);
        expect(func).toHaveBeenCalledTimes(1);

        const [result1, result2] = await Promise.all([promise1, promise2]);
        expect(result1).toBe('result');
        expect(result2).toBe('result');
    });

    it('should use default wait time if not specified', async () => {
        const func = vi.fn().mockReturnValue('result');
        const debouncedFunc = debounce(func);

        const promise = debouncedFunc();
        vi.advanceTimersByTime(299);
        expect(func).not.toHaveBeenCalled();

        vi.advanceTimersByTime(1);
        expect(func).toHaveBeenCalledTimes(1);

        const result = await promise;
        expect(result).toBe('result');
    });

    it('should maintain correct this context', async () => {
        const context = {
            value: 'test',
            method: vi.fn(function(this: { value: string }) {
                return this.value;
            })
        };

        const debouncedMethod = debounce(context.method.bind(context), 100);
        const promise = debouncedMethod();

        vi.advanceTimersByTime(100);
        expect(context.method).toHaveBeenCalledTimes(1);

        const result = await promise;
        expect(result).toBe('test');
    });

    it('should handle synchronous errors', async () => {
        const error = new Error('Sync error');
        const func = vi.fn().mockImplementation(() => {
            throw error;
        });
        const debouncedFunc = debounce(func, 100);

        const promise = debouncedFunc();
        vi.advanceTimersByTime(100);

        await expect(promise).rejects.toThrow(error);
    });

    it('should handle multiple calls with different arguments', async () => {
        const func = vi.fn().mockImplementation((...args: number[]) => args.reduce((a, b) => a + b, 0));
        const debouncedFunc = debounce(func, 100);

        const promise1 = debouncedFunc(1, 2);
        const promise2 = debouncedFunc(3, 4);
        const promise3 = debouncedFunc(5, 6);

        vi.advanceTimersByTime(100);
        expect(func).toHaveBeenCalledWith(5, 6);

        const [result1, result2, result3] = await Promise.all([promise1, promise2, promise3]);
        expect(result1).toBe(11); // 5 + 6
        expect(result2).toBe(11); // 5 + 6
        expect(result3).toBe(11); // 5 + 6
    });
});
