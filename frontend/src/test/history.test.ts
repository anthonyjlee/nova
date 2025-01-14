import { describe, it, expect } from 'vitest';
import { TaskState } from '$lib/types/task';
import {
    createStateChangeEvent,
    createUpdateEvent,
    createCommentEvent,
    createAssignmentEvent,
    createAgentInteraction,
    initializeTaskHistory,
    initializeHistoryMetrics,
    validateStateHistory,
    validateUpdateHistory,
    validateComments,
    validateAssignmentHistory,
    validateAgentInteractions,
    validateTaskHistory,
    validateHistoryMetrics,
    type StateChangeEvent,
    type UpdateEvent,
    type CommentEvent,
    type AssignmentEvent,
    type AgentInteraction,
    type TaskHistory,
    type HistoryMetrics
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
                task_id: 'task-123',
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
                ],
                agent_interactions: [
                    createAgentInteraction('message', 'Agent response')
                ],
                metadata: {}
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
            const history = initializeTaskHistory('task-123');
            expect(history.task_id).toBe('task-123');
            expect(history.state_history).toHaveLength(0);
            expect(history.update_history).toHaveLength(0);
            expect(history.comments).toHaveLength(0);
            expect(history.assignment_history).toHaveLength(0);
            expect(history.agent_interactions).toHaveLength(0);
            expect(history.metadata).toEqual({});
            expect(validateTaskHistory(history)).toBe(true);
        });

        it('should initialize history metrics', () => {
            const metrics = initializeHistoryMetrics();
            expect(metrics.total_events).toBe(0);
            expect(metrics.state_changes).toBe(0);
            expect(metrics.updates).toBe(0);
            expect(metrics.comments).toBe(0);
            expect(metrics.assignments).toBe(0);
            expect(metrics.agent_interactions).toBe(0);
            expect(metrics.average_time_in_state).toEqual({
                pending: 0,
                in_progress: 0,
                blocked: 0,
                completed: 0
            });
            expect(metrics.metadata).toEqual({});
            expect(validateHistoryMetrics(metrics)).toBe(true);
        });
    });

    describe('Agent Interactions', () => {
        it('should create and validate agent interactions', () => {
            const interaction = createAgentInteraction(
                'message',
                'Agent response',
                { context: 'test' },
                { importance: 'high' }
            );
            expect(interaction.type).toBe('message');
            expect(interaction.content).toBe('Agent response');
            expect(interaction.context).toEqual({ context: 'test' });
            expect(interaction.metadata).toEqual({ importance: 'high' });
            expect(validateAgentInteractions([interaction])).toBe(true);
        });

        it('should validate different interaction types', () => {
            const messageInteraction = createAgentInteraction('message', 'Message content');
            const taskInteraction = createAgentInteraction('task', 'Task update');
            const actionInteraction = createAgentInteraction('action', 'Action performed');

            expect(validateAgentInteractions([
                messageInteraction,
                taskInteraction,
                actionInteraction
            ])).toBe(true);
        });
    });

    describe('Type Validation', () => {
        it('should validate agent interaction type', () => {
            const interaction: AgentInteraction = {
                id: 'test-id',
                type: 'message',
                content: 'Test content',
                timestamp: new Date().toISOString(),
                metadata: {}
            };
            expect(validateAgentInteractions([interaction])).toBe(true);
        });

        it('should validate history metrics type', () => {
            const metrics: HistoryMetrics = {
                total_events: 0,
                state_changes: 0,
                updates: 0,
                comments: 0,
                assignments: 0,
                agent_interactions: 0,
                average_time_in_state: {
                    pending: 0,
                    in_progress: 0,
                    blocked: 0,
                    completed: 0
                },
                metadata: {}
            };
            expect(validateHistoryMetrics(metrics)).toBe(true);
        });
    });

    describe('Validation Edge Cases', () => {
        it('should reject invalid timestamps', () => {
            const event = createStateChangeEvent(TaskState.PENDING, TaskState.IN_PROGRESS);
            event.timestamp = 'invalid-date';
            expect(validateStateHistory([event])).toBe(false);
        });

        it('should reject malformed event IDs', () => {
            const event = createCommentEvent('Test', 'user1');
            event.id = '';
            expect(validateComments([event])).toBe(false);
        });

        it('should reject missing required fields', () => {
            const event = createUpdateEvent('label', 'old', 'new') as Partial<UpdateEvent>;
            delete event.field;
            expect(validateUpdateHistory([event])).toBe(false);
        });

        it('should reject invalid state transitions', () => {
            const event = createStateChangeEvent(TaskState.PENDING, 'invalid-state' as TaskState);
            expect(validateStateHistory([event])).toBe(false);
        });
    });

    describe('History Metrics', () => {
        it('should calculate time in state', () => {
            const metrics = initializeHistoryMetrics();
            const now = new Date();
            const hourAgo = new Date(now.getTime() - 3600000);
            
            metrics.average_time_in_state.pending = hourAgo.getTime();
            expect(metrics.average_time_in_state.pending).toBe(hourAgo.getTime());
        });

        it('should track event counts', () => {
            const metrics = initializeHistoryMetrics();
            metrics.state_changes = 1;
            metrics.comments = 2;
            metrics.updates = 3;
            metrics.assignments = 4;
            metrics.agent_interactions = 5;
            metrics.total_events = 15;

            expect(validateHistoryMetrics(metrics)).toBe(true);
            expect(metrics.total_events).toBe(15);
        });

        it('should handle metrics updates', () => {
            const metrics = initializeHistoryMetrics();
            metrics.state_changes++;
            metrics.total_events++;
            expect(metrics.state_changes).toBe(1);
            expect(metrics.total_events).toBe(1);
        });
    });

    describe('Performance', () => {
        it('should handle large history validation', () => {
            const largeHistory: TaskHistory = {
                task_id: 'task-123',
                state_history: Array(100).fill(null).map(() => 
                    createStateChangeEvent(TaskState.PENDING, TaskState.IN_PROGRESS)
                ),
                update_history: Array(100).fill(null).map(() =>
                    createUpdateEvent('label', 'old', 'new')
                ),
                comments: Array(100).fill(null).map(() =>
                    createCommentEvent('Test comment', 'user1')
                ),
                assignment_history: Array(100).fill(null).map(() =>
                    createAssignmentEvent('user1', 'user2')
                ),
                agent_interactions: Array(100).fill(null).map(() =>
                    createAgentInteraction('message', 'Test')
                ),
                metadata: {}
            };

            expect(validateTaskHistory(largeHistory)).toBe(true);
        });

        it('should handle concurrent updates', () => {
            const history = initializeTaskHistory('task-123');
            const updates = Array(10).fill(null).map(() => 
                createUpdateEvent('field' + Math.random(), 'old', 'new')
            );
            history.update_history = updates;
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
