import { describe, it, expect } from 'vitest';
import {
    validateTask,
    validateTaskDetails,
    validateMessage,
    validateMessageRequest,
    validateSubTask,
    validateComment,
    validateMetadata,
    isValidISODate,
    assertValid,
    ValidationError,
    validateTaskUpdate,
    validateTaskSearch,
    validateTaskSearchResult,
    schemas
} from '$lib/utils/validation';
import { TaskState } from '$lib/types/task';
import type { Task, TaskDetails, Comment } from '$lib/types/task';
import type { Message, MessageRequest, TaskUpdate, TaskSearchMessage, TaskSearchResultMessage } from '$lib/types/websocket';
import type { SubTask } from '$lib/types/subtask';
import { createDefaultPagination, createDefaultSort } from '$lib/types/search';

describe('Validation', () => {
    // Test data
    const now = new Date().toISOString();
    const validTask: Task = {
        id: '123',
        label: 'Test Task',
        type: 'task',
        status: TaskState.PENDING,
        created_at: now,
        updated_at: now,
        metadata: {},
        description: 'Test description',
        team_id: 'team1',
        domain: 'test',
        title: 'Test Title',
        priority: 'high',
        assignee: 'user1',
        dueDate: now,
        tags: ['test'],
        time_active: 0,
        dependencies: ['456'],
        blocked_by: ['789'],
        sub_tasks: [{
            id: 'sub1',
            description: 'Subtask 1',
            completed: false,
            created_at: now
        }],
        completed: false
    };

    const validMessage: Message = {
        type: 'message',
        id: '123',
        content: 'Test message',
        sender_type: 'user',
        sender_id: 'user1',
        timestamp: now,
        metadata: {}
    };

    const validTaskUpdate: TaskUpdate = {
        type: 'task_update',
        data: validTask,
        timestamp: now
    };

    const validTaskSearch: TaskSearchMessage = {
        type: 'task_search',
        data: {
            text: 'test',
            filter: {},
            sort: createDefaultSort(),
            pagination: createDefaultPagination()
        },
        timestamp: now
    };

    const validTaskSearchResult: TaskSearchResultMessage = {
        type: 'task_search_result',
        result: {
            items: [validTask],
            pagination: {
                page: 1,
                pageSize: 10,
                totalItems: 1,
                totalPages: 1
            }
        },
        timestamp: now
    };

    const validMessageRequest: MessageRequest = {
        content: 'Test message',
        thread_id: 'thread1',
        sender_type: 'user',
        sender_id: 'user1',
        metadata: {}
    };

    const validSubTask: SubTask = {
        id: 'sub1',
        description: 'Test subtask',
        completed: false,
        created_at: now
    };

    const validComment: Comment = {
        id: 'comment1',
        content: 'Test comment',
        author: 'user1',
        timestamp: now,
        edited: false
    };

    const validTaskDetails: TaskDetails = {
        task: validTask,
        dependencies: [],
        blocked_by: [],
        sub_tasks: [],
        comments: [],
        domain_access: ['general']
    };

    describe('Task Update Validation', () => {
        it('should validate a valid task update', () => {
            expect(validateTaskUpdate(validTaskUpdate)).toBe(true);
        });

        it('should reject update with wrong type', () => {
            const invalidUpdate = {
                ...validTaskUpdate,
                type: 'wrong_type'
            } as unknown as Partial<TaskUpdate>;
            expect(validateTaskUpdate(invalidUpdate)).toBe(false);
        });

        it('should reject update with missing data', () => {
            const invalidUpdate = { ...validTaskUpdate, data: undefined };
            expect(validateTaskUpdate(invalidUpdate)).toBe(false);
        });

        it('should reject update with invalid task data', () => {
            const invalidUpdate = {
                ...validTaskUpdate,
                data: { ...validTask, id: '' }
            };
            expect(validateTaskUpdate(invalidUpdate)).toBe(false);
        });

        it('should reject update with invalid timestamp', () => {
            const invalidUpdate = { ...validTaskUpdate, timestamp: 'invalid-date' };
            expect(validateTaskUpdate(invalidUpdate)).toBe(false);
        });
    });

    describe('Task Search Validation', () => {
        it('should validate a valid task search', () => {
            expect(validateTaskSearch(validTaskSearch)).toBe(true);
        });

        it('should reject search with wrong type', () => {
            const invalidSearch = {
                ...validTaskSearch,
                type: 'wrong_type'
            } as unknown as Partial<TaskSearchMessage>;
            expect(validateTaskSearch(invalidSearch)).toBe(false);
        });

        it('should reject search with missing data', () => {
            const invalidSearch = { ...validTaskSearch, data: undefined };
            expect(validateTaskSearch(invalidSearch)).toBe(false);
        });

        it('should reject search with invalid timestamp', () => {
            const invalidSearch = { ...validTaskSearch, timestamp: 'invalid-date' };
            expect(validateTaskSearch(invalidSearch)).toBe(false);
        });
    });

    describe('Task Search Result Validation', () => {
        it('should validate a valid task search result', () => {
            expect(validateTaskSearchResult(validTaskSearchResult)).toBe(true);
        });

        it('should reject result with wrong type', () => {
            const invalidResult = {
                ...validTaskSearchResult,
                type: 'wrong_type'
            } as unknown as Partial<TaskSearchResultMessage>;
            expect(validateTaskSearchResult(invalidResult)).toBe(false);
        });

        it('should reject result with missing result data', () => {
            const invalidResult = { ...validTaskSearchResult, result: undefined };
            expect(validateTaskSearchResult(invalidResult)).toBe(false);
        });

        it('should reject result with invalid timestamp', () => {
            const invalidResult = { ...validTaskSearchResult, timestamp: 'invalid-date' };
            expect(validateTaskSearchResult(invalidResult)).toBe(false);
        });
    });

    describe('Message Validation', () => {
        it('should validate a valid message', () => {
            expect(validateMessage(validMessage)).toBe(true);
        });

        it('should reject message with missing required fields', () => {
            const invalidMessage = { ...validMessage, id: undefined };
            expect(validateMessage(invalidMessage)).toBe(false);
        });

        it('should reject message with invalid timestamp', () => {
            const invalidMessage = { ...validMessage, timestamp: 'invalid-date' };
            expect(validateMessage(invalidMessage)).toBe(false);
        });

        it('should validate metadata', () => {
            const messageWithMetadata = {
                ...validMessage,
                metadata: { key: 'value', nested: { key: 'value' } }
            };
            expect(validateMessage(messageWithMetadata)).toBe(true);
        });
    });

    describe('Message Request Validation', () => {
        it('should validate a valid message request', () => {
            expect(validateMessageRequest(validMessageRequest)).toBe(true);
        });

        it('should reject request with missing required fields', () => {
            const invalidRequest = { ...validMessageRequest, content: undefined };
            expect(validateMessageRequest(invalidRequest)).toBe(false);
        });

        it('should validate optional fields', () => {
            const requestWithOptionals = {
                ...validMessageRequest,
                sender_type: undefined,
                metadata: undefined
            };
            expect(validateMessageRequest(requestWithOptionals)).toBe(true);
        });
    });

    describe('SubTask Validation', () => {
        it('should validate a valid subtask', () => {
            expect(validateSubTask(validSubTask)).toBe(true);
        });

        it('should reject subtask with missing required fields', () => {
            const invalidSubTask = { ...validSubTask, id: undefined };
            expect(validateSubTask(invalidSubTask)).toBe(false);
        });

        it('should validate optional fields', () => {
            const subtaskWithOptionals = {
                ...validSubTask,
                completed: undefined,
                created_at: undefined
            };
            expect(validateSubTask(subtaskWithOptionals)).toBe(true);
        });
    });

    describe('Comment Validation', () => {
        it('should validate a valid comment', () => {
            expect(validateComment(validComment)).toBe(true);
        });

        it('should reject comment with missing required fields', () => {
            const invalidComment = { ...validComment, id: undefined };
            expect(validateComment(invalidComment)).toBe(false);
        });

        it('should validate optional fields', () => {
            const commentWithOptionals = {
                ...validComment,
                edited: undefined
            };
            expect(validateComment(commentWithOptionals)).toBe(true);
        });
    });

    describe('Metadata Validation', () => {
        it('should validate valid metadata', () => {
            const validMetadata = {
                string: 'value',
                number: 123,
                boolean: true,
                nested: {
                    key: 'value'
                },
                array: [1, 2, 3]
            };
            expect(validateMetadata(validMetadata)).toBe(true);
        });

        it('should reject invalid metadata', () => {
            const invalidMetadata = {
                undefined: undefined,
                function: () => {},
                symbol: Symbol('test')
            };
            expect(validateMetadata(invalidMetadata)).toBe(false);
        });

        it('should validate nested metadata', () => {
            const nestedMetadata = {
                level1: {
                    level2: {
                        level3: 'value'
                    }
                }
            };
            expect(validateMetadata(nestedMetadata)).toBe(true);
        });
    });

    describe('Date Validation', () => {
        it('should validate ISO date strings', () => {
            expect(isValidISODate(now)).toBe(true);
        });

        it('should reject invalid date strings', () => {
            expect(isValidISODate('invalid-date')).toBe(false);
            expect(isValidISODate('2023-13-45')).toBe(false);
            expect(isValidISODate('')).toBe(false);
        });
    });

    describe('Task Validation', () => {
        it('should validate a valid task', () => {
            expect(validateTask(validTask)).toBe(true);
        });

        it('should reject a task with missing id', () => {
            const invalidTask = { ...validTask, id: undefined };
            expect(validateTask(invalidTask)).toBe(false);
        });

        it('should reject a task with invalid status', () => {
            const invalidTask = { ...validTask, status: 'invalid' as TaskState };
            expect(validateTask(invalidTask)).toBe(false);
        });

        it('should reject a task with missing label', () => {
            const invalidTask = { ...validTask, label: undefined };
            expect(validateTask(invalidTask)).toBe(false);
        });

        it('should reject a task with invalid metadata', () => {
            const invalidTask = { ...validTask, metadata: undefined };
            expect(validateTask(invalidTask)).toBe(false);
        });
    });

    describe('Task Details Validation', () => {
        it('should validate valid task details', () => {
            expect(validateTaskDetails(validTaskDetails)).toBe(true);
        });

        it('should reject details with invalid task', () => {
            const invalidDetails = {
                ...validTaskDetails,
                task: { ...validTask, id: '' }
            };
            expect(validateTaskDetails(invalidDetails)).toBe(false);
        });

        it('should reject details with non-array dependencies', () => {
            const invalidDetails = {
                ...validTaskDetails,
                dependencies: undefined
            } as Partial<TaskDetails>;
            expect(validateTaskDetails(invalidDetails)).toBe(false);
        });

        it('should reject details with non-array blocked_by', () => {
            const invalidDetails = {
                ...validTaskDetails,
                blocked_by: undefined
            } as Partial<TaskDetails>;
            expect(validateTaskDetails(invalidDetails)).toBe(false);
        });
    });

    describe('Assert Valid', () => {
        it('should not throw for valid data', () => {
            expect(() => assertValid(validTask, schemas.TaskSchema, 'Invalid task')).not.toThrow();
        });

        it('should throw ValidationError for invalid data', () => {
            const invalidTask = { ...validTask, id: '' };
            expect(() => assertValid(invalidTask, schemas.TaskSchema, 'Invalid task'))
                .toThrow(ValidationError);
        });

        it('should include details in error', () => {
            const invalidTask = { ...validTask, id: '' };
            try {
                assertValid(invalidTask, schemas.TaskSchema, 'Invalid task');
            } catch (error) {
                expect(error).toBeInstanceOf(ValidationError);
                expect((error as ValidationError).details).toBeDefined();
                expect((error as ValidationError).details?.value).toEqual(invalidTask);
            }
        });
    });
});
