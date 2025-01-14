import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import SearchInput from '$lib/components/search/SearchInput.svelte';
import { createSearchQuery } from '$lib/types/search';

describe('SearchInput', () => {
    beforeEach(() => {
        vi.useFakeTimers();
    });

    afterEach(() => {
        vi.useRealTimers();
    });

    it('should render with default placeholder', () => {
        const { getByPlaceholderText } = render(SearchInput);
        expect(getByPlaceholderText('Search tasks...')).toBeTruthy();
    });

    it('should render with custom placeholder', () => {
        const { getByPlaceholderText } = render(SearchInput, {
            props: { placeholder: 'Custom placeholder' }
        });
        expect(getByPlaceholderText('Custom placeholder')).toBeTruthy();
    });

    it('should initialize with initial query', () => {
        const { getByDisplayValue } = render(SearchInput, {
            props: { initialQuery: 'initial search' }
        });
        expect(getByDisplayValue('initial search')).toBeTruthy();
    });

    it('should show clear button when text is entered', async () => {
        const { getByTestId, queryByTestId } = render(SearchInput);
        const input = getByTestId('search-input');

        expect(queryByTestId('clear-search')).toBeNull();

        await fireEvent.input(input, { target: { value: 'test' } });
        expect(queryByTestId('clear-search')).toBeTruthy();
    });

    it('should clear text when clear button is clicked', async () => {
        const { getByTestId } = render(SearchInput);
        const input = getByTestId('search-input');

        await fireEvent.input(input, { target: { value: 'test' } });
        await fireEvent.click(getByTestId('clear-search'));

        expect(input).toHaveValue('');
    });

    it('should debounce search event', async () => {
        const { getByTestId, component } = render(SearchInput, {
            props: { debounceMs: 500 }
        });
        const mockSearch = vi.fn();
        component.$on('search', mockSearch);

        const input = getByTestId('search-input');
        await fireEvent.input(input, { target: { value: 'test' } });

        expect(mockSearch).not.toHaveBeenCalled();

        vi.advanceTimersByTime(499);
        expect(mockSearch).not.toHaveBeenCalled();

        vi.advanceTimersByTime(1);
        expect(mockSearch).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: createSearchQuery('test')
            })
        );
    });

    it('should trigger immediate search on Enter', async () => {
        const { getByTestId, component } = render(SearchInput, {
            props: { debounceMs: 500 }
        });
        const mockSearch = vi.fn();
        component.$on('search', mockSearch);

        const input = getByTestId('search-input');
        await fireEvent.input(input, { target: { value: 'test' } });
        await fireEvent.keyDown(input, { key: 'Enter' });

        expect(mockSearch).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: createSearchQuery('test')
            })
        );
        expect(mockSearch).toHaveBeenCalledTimes(1);
    });

    it('should clear on Escape key', async () => {
        const { getByTestId, component } = render(SearchInput);
        const mockClear = vi.fn();
        component.$on('clear', mockClear);

        const input = getByTestId('search-input');
        await fireEvent.input(input, { target: { value: 'test' } });
        await fireEvent.keyDown(input, { key: 'Escape' });

        expect(input).toHaveValue('');
        expect(mockClear).toHaveBeenCalled();
    });

    it('should emit clear event when cleared', async () => {
        const { getByTestId, component } = render(SearchInput);
        const mockClear = vi.fn();
        component.$on('clear', mockClear);

        const input = getByTestId('search-input');
        await fireEvent.input(input, { target: { value: 'test' } });
        await fireEvent.click(getByTestId('clear-search'));

        expect(mockClear).toHaveBeenCalled();
    });

    it('should handle rapid typing correctly', async () => {
        const { getByTestId, component } = render(SearchInput, {
            props: { debounceMs: 300 }
        });
        const mockSearch = vi.fn();
        component.$on('search', mockSearch);

        const input = getByTestId('search-input');

        // Type 'test' rapidly
        await fireEvent.input(input, { target: { value: 't' } });
        vi.advanceTimersByTime(100);
        await fireEvent.input(input, { target: { value: 'te' } });
        vi.advanceTimersByTime(100);
        await fireEvent.input(input, { target: { value: 'tes' } });
        vi.advanceTimersByTime(100);
        await fireEvent.input(input, { target: { value: 'test' } });

        // Only the final value should trigger a search after debounce
        vi.advanceTimersByTime(300);
        expect(mockSearch).toHaveBeenCalledTimes(1);
        expect(mockSearch).toHaveBeenCalledWith(
            expect.objectContaining({
                detail: createSearchQuery('test')
            })
        );
    });

    it('should cleanup timeout on destroy', () => {
        const { component } = render(SearchInput);
        const clearTimeoutSpy = vi.spyOn(global, 'clearTimeout');

        component.$destroy();
        expect(clearTimeoutSpy).toHaveBeenCalled();
    });
});
