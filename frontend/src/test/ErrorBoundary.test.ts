import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import ErrorBoundary from '$lib/components/shared/ErrorBoundary.svelte';
import { ValidationError } from '$lib/utils/validation';

describe('ErrorBoundary', () => {
    // Mock console.error to prevent test output noise
    const originalConsoleError = console.error;
    beforeEach(() => {
        console.error = vi.fn();
    });
    afterEach(() => {
        console.error = originalConsoleError;
    });

    it('should render children when there is no error', () => {
        const { getByText } = render(ErrorBoundary, {
            props: {
                class_name: '',
                showDetails: false
            },
            // @ts-expect-error - Svelte typing issue with slots in test environment
            slots: {
                default: '<div>Test Content</div>'
            }
        });

        expect(getByText('Test Content')).toBeTruthy();
    });

    it('should display error message when handleError is called', async () => {
        const error = new Error('Test error message');
        const { component, getByText } = render(ErrorBoundary);

        // Access the component instance
        const instance = component as unknown as {
            handleError: (e: Error | ValidationError) => void;
            resetError: () => void;
        };
        
        // Call handleError
        instance.handleError(error);

        // Error message should be displayed
        expect(getByText('Something went wrong')).toBeTruthy();
        expect(getByText('Test error message')).toBeTruthy();
    });

    it('should display validation error details when showDetails is true', async () => {
        const error = new ValidationError('Invalid data', { 
            field: 'test',
            value: 'invalid'
        });
        
        const { component, getByText } = render(ErrorBoundary, {
            props: { showDetails: true }
        });

        // Access the component instance
        const instance = component as unknown as {
            handleError: (e: Error | ValidationError) => void;
            resetError: () => void;
        };
        
        // Call handleError
        instance.handleError(error);

        // Error details should be displayed
        expect(getByText('Something went wrong')).toBeTruthy();
        expect(getByText('Invalid data')).toBeTruthy();
        expect(getByText(JSON.stringify({ field: 'test', value: 'invalid' }, null, 2))).toBeTruthy();
    });

    it('should not display error details when showDetails is false', async () => {
        const error = new ValidationError('Invalid data', { 
            field: 'test',
            value: 'invalid'
        });
        
        const { component, getByText, queryByText } = render(ErrorBoundary, {
            props: { showDetails: false }
        });

        // Access the component instance
        const instance = component as unknown as {
            handleError: (e: Error | ValidationError) => void;
            resetError: () => void;
        };
        
        // Call handleError
        instance.handleError(error);

        // Error message should be displayed but not details
        expect(getByText('Something went wrong')).toBeTruthy();
        expect(getByText('Invalid data')).toBeTruthy();
        expect(queryByText(JSON.stringify({ field: 'test', value: 'invalid' }, null, 2))).toBeFalsy();
    });

    it('should reset error state when Try Again is clicked', async () => {
        const error = new Error('Test error message');
        const { component, getByText, queryByText } = render(ErrorBoundary);

        // Access the component instance
        const instance = component as unknown as {
            handleError: (e: Error | ValidationError) => void;
            resetError: () => void;
        };
        
        // Call handleError
        instance.handleError(error);

        // Error should be displayed
        expect(getByText('Something went wrong')).toBeTruthy();

        // Click Try Again button
        await fireEvent.click(getByText('Try Again'));

        // Error should be cleared
        expect(queryByText('Something went wrong')).toBeFalsy();
    });

    it('should log errors to console', async () => {
        const error = new Error('Test error message');
        const { component } = render(ErrorBoundary);

        // Access the component instance
        const instance = component as unknown as {
            handleError: (e: Error | ValidationError) => void;
            resetError: () => void;
        };
        
        // Call handleError
        instance.handleError(error);

        // Error should be logged
        expect(console.error).toHaveBeenCalledWith('Error caught by boundary:', error);
    });
});
