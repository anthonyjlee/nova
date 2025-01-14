import { expect } from 'vitest';
import type { Task } from '$lib/types/task';
import { TaskState } from '$lib/types/task';
import type { WebSocketMessage } from '$lib/types/websocket';
import type { ValidationError } from '$lib/utils/validation';

export const wait = {
    forAnimation: () => new Promise(resolve => requestAnimationFrame(resolve)),
    forTransition: () => new Promise(resolve => setTimeout(resolve, 50)),
    forWebSocket: () => new Promise(resolve => setTimeout(resolve, 100)),
    forNextTick: () => new Promise(resolve => setTimeout(resolve, 0))
};

export const assertions = {
    taskExists: (tasks: Task[], id: string) => {
        const task = tasks.find(t => t.id === id);
        expect(task).toBeDefined();
        return task!;
    },
    taskHasStatus: (tasks: Task[], id: string, status: TaskState) => {
        const task = assertions.taskExists(tasks, id);
        expect(task.status).toBe(status);
    },
    websocketIsConnected: (websocket: { isConnected: boolean }) => {
        expect(websocket.isConnected).toBe(true);
    },
    errorBoundaryHasError: (errorBoundary: { errors: (Error | ValidationError)[] }, errorType: { new(message: string, details?: Record<string, unknown>): Error | ValidationError }) => {
        expect(errorBoundary.errors.some(e => e instanceof errorType)).toBe(true);
    }
};

export class TestContext {
    public errorBoundary = {
        errors: [] as (Error | ValidationError)[],
        handleError(error: Error | ValidationError) {
            this.errors.push(error);
        }
    };

    reset() {
        this.errorBoundary.errors = [];
    }
}

export class TaskTestContext extends TestContext {
    public generateId = () => Math.random().toString(36).substr(2, 9);
    public websocket = {
        isConnected: false,
        handlers: new Map<string, ((event: WebSocketMessage) => void)[]>(),
        connect() {
            this.isConnected = true;
        },
        disconnect() {
            this.isConnected = false;
        },
        addEventListener(event: string, callback: (event: WebSocketMessage) => void) {
            if (!this.handlers.has(event)) {
                this.handlers.set(event, []);
            }
            this.handlers.get(event)?.push(callback);
        },
        removeEventListener(event: string, callback: (event: WebSocketMessage) => void) {
            const handlers = this.handlers.get(event);
            if (handlers) {
                const index = handlers.indexOf(callback);
                if (index > -1) {
                    handlers.splice(index, 1);
                }
            }
        },
        send(message: WebSocketMessage) {
            const handlers = this.handlers.get(message.type);
            if (handlers) {
                handlers.forEach(handler => handler(message));
            }
        }
    };

    addTask(overrides: Partial<Task> = {}) {
        const task: Task = {
            id: crypto.randomUUID(),
            label: 'Test Task',
            type: 'task',
            status: TaskState.PENDING,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            metadata: {},
            ...overrides
        };
        const message = {
            type: 'task_update' as const,
            data: task,
            timestamp: new Date().toISOString()
        };
        this.websocket.send(message);
        return task;
    }

    updateTask(id: string, updates: Partial<Task>) {
        const task = this.addTask({ id, ...updates });
        const message = {
            type: 'task_update' as const,
            data: task,
            timestamp: new Date().toISOString()
        };
        this.websocket.send(message);
        return task;
    }

    reset() {
        super.reset();
        this.websocket.isConnected = false;
        this.websocket.handlers.clear();
    }
}
