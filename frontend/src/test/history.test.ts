import { describe, it, expect } from 'vitest';
import { TaskState } from '$lib/types/task';
import {
    createStateChangeEvent,
    createUpdateEvent,
    createCommentEvent,
    createAssignmentEvent,
    initializeTaskHistory,
    validateStateHistory,
    validateUpdateHistory,
    validateComments,
    validateAssignmentHistory,
    validateTaskHistory,
    type StateChangeEvent,
    type UpdateEvent,
    type CommentEvent,
    type AssignmentEvent,
    type TaskHistory
} from '$lib/types/history';

describe('History Types', () => {
    describe('Event Creation', () => {
        it('should create valid state change event', () => {
            const event = createStateChangeEvent(TaskState.PENDING, TaskState.IN_PROGRESS);
            expect(event.from).toBe(TaskState.PENDING);
            expect(event.to).toBe(TaskState.IN_PROGRESS);
            expect(event.timestamp).toBeDefined();
        });

        it('should create valid update event', () => {
            const event = createUpdateEvent('label', 'old label', 'new label');
            expect(event.field).toBe('label');
            expect(event.from).toBe('old label');
            expect(event.to).toBe('new label');
            expect(event.timestamp).toBeDefined();
        });

        it('should create valid comment event', () => {
            const event = createCommentEvent('Test comment', 'user1');
            expect(event.content).toBe('Test comment');
            expect(event.author).toBe('user1');
            expect(event.id).toBeDefined();
            expect(event.timestamp).toBeDefined();
        });

        it('should create valid assignment event', () => {
            const event = createAssignmentEvent('user1', 'user2', 'Reassignment');
            expect(event.from).toBe('user1');
            expect(event.to).toBe('user2');
            expect(event.reason).toBe('Reassignment');
            expect(event.timestamp).toBeDefined();
        });
    });

    describe('History Validation', () => {
        it('should validate state history', () => {
            const validHistory: StateChangeEvent[] = [
                createStateChangeEvent(TaskState.PENDING, TaskState.IN_PROGRESS),
                createStateChangeEvent(TaskState.IN_PROGRESS, TaskState.COMPLETED)
            ];

            const invalidHistory = [
                { from: 'invalid', to: TaskState.IN_PROGRESS, timestamp: new Date().toISOString() }
            ];

            expect(validateStateHistory(validHistory)).toBe(true);
            expect(validateStateHistory(invalidHistory)).toBe(false);
        });

        it('should validate update history', () => {
            const validHistory: UpdateEvent[] = [
                createUpdateEvent('label', 'old', 'new'),
                createUpdateEvent('priority', 'low', 'high')
            ];

            const invalidHistory = [
                { field: 'label', timestamp: new Date().toISOString() }
            ];

            expect(validateUpdateHistory(validHistory)).toBe(true);
            expect(validateUpdateHistory(invalidHistory)).toBe(false);
        });

        it('should validate comments', () => {
            const validComments: CommentEvent[] = [
                createCommentEvent('Comment 1', 'user1'),
                createCommentEvent('Comment 2', 'user2')
            ];

            const invalidComments = [
                { content: 'Invalid comment' }
            ];

            expect(validateComments(validComments)).toBe(true);
            expect(validateComments(invalidComments)).toBe(false);
        });

        it('should validate assignment history', () => {
            const validHistory: AssignmentEvent[] = [
                createAssignmentEvent('user1', 'user2'),
                createAssignmentEvent('user2', null)
            ];

            const invalidHistory = [
                { from: 'user1', timestamp: new Date().toISOString() }
            ];

            expect(validateAssignmentHistory(validHistory)).toBe(true);
            expect(validateAssignmentHistory(invalidHistory)).toBe(false);
        });

        it('should validate complete task history', () => {
            const validHistory: TaskHistory = {
                state_history: [
                    createStateChangeEvent(TaskState.PENDING, TaskState.IN_PROGRESS)
                ],
                update_history: [
                    createUpdateEvent('label', 'old', 'new')
                ],
                comments: [
                    createCommentEvent('Test comment', 'user1')
                ],
                assignment_history: [
                    createAssignmentEvent('user1', 'user2')
                ]
            };

            const invalidHistory = {
                state_history: [{ invalid: true }],
                update_history: [],
                comments: [],
                assignment_history: []
            };

            expect(validateTaskHistory(validHistory)).toBe(true);
            expect(validateTaskHistory(invalidHistory)).toBe(false);
        });
    });

    describe('History Initialization', () => {
        it('should create empty task history', () => {
            const history = initializeTaskHistory();
            expect(history.state_history).toHaveLength(0);
            expect(history.update_history).toHaveLength(0);
            expect(history.comments).toHaveLength(0);
            expect(history.assignment_history).toHaveLength(0);
            expect(validateTaskHistory(history)).toBe(true);
        });
    });

    describe('Edge Cases', () => {
        it('should handle null values in update events', () => {
            const event = createUpdateEvent('description', 'old', null);
            expect(event.to).toBeNull();
            expect(validateUpdateHistory([event])).toBe(true);
        });

        it('should handle unassignment in assignment events', () => {
            const event = createAssignmentEvent('user1', null);
            expect(event.to).toBeNull();
            expect(validateAssignmentHistory([event])).toBe(true);
        });

        it('should handle edited comments', () => {
            const event = createCommentEvent('Original comment', 'user1');
            event.edited = true;
            expect(validateComments([event])).toBe(true);
        });

        it('should handle invalid input types', () => {
            expect(validateTaskHistory(null)).toBe(false);
            expect(validateTaskHistory(undefined)).toBe(false);
            expect(validateTaskHistory(42)).toBe(false);
            expect(validateTaskHistory('not an object')).toBe(false);
            expect(validateTaskHistory([])).toBe(false);
        });
    });
});
