import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const transitionRate = new Rate('transitions');

// Test configuration
export const options = {
    stages: [
        { duration: '1m', target: 10 },  // Ramp up to 10 users
        { duration: '3m', target: 10 },  // Stay at 10 users
        { duration: '1m', target: 0 },   // Ramp down to 0 users
    ],
    thresholds: {
        'http_req_duration': ['p(95)<500'], // 95% of requests must complete within 500ms
        'errors': ['rate<0.1'],             // Error rate must be less than 10%
        'transitions': ['rate>0.9'],        // Successful transition rate must be above 90%
    },
};

// Helper to get next valid state
function getNextState(currentState) {
    const validTransitions = {
        'pending': ['in_progress', 'completed'],
        'in_progress': ['blocked', 'completed'],
        'blocked': ['in_progress', 'completed'],
        'completed': []
    };
    const possibleStates = validTransitions[currentState];
    return possibleStates[Math.floor(Math.random() * possibleStates.length)];
}

// Initialize test data
const BASE_URL = 'http://localhost:8000/api';
let taskIds = [];

export function setup() {
    // Create test tasks
    for (let i = 0; i < 5; i++) {
        const response = http.post(`${BASE_URL}/tasks/graph/addNode`, JSON.stringify({
            id: `perf_test_${i}`,
            label: `Performance Test Task ${i}`,
            type: 'task',
            status: 'pending'
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
        
        if (response.status === 200) {
            taskIds.push(`perf_test_${i}`);
        }
    }
    
    return { taskIds };
}

export default function(data) {
    // Randomly select a task
    const taskId = data.taskIds[Math.floor(Math.random() * data.taskIds.length)];
    
    // Get current task state
    const taskResponse = http.get(`${BASE_URL}/tasks/${taskId}/details`);
    const taskCheck = check(taskResponse, {
        'task details retrieved': (r) => r.status === 200,
    });
    if (!taskCheck) errorRate.add(1);
    
    if (taskResponse.status === 200) {
        const task = JSON.parse(taskResponse.body);
        const nextState = getNextState(task.status);
        
        if (nextState) {
            // Attempt state transition
            const transitionResponse = http.post(
                `${BASE_URL}/tasks/${taskId}/transition`,
                JSON.stringify({ new_state: nextState }),
                { headers: { 'Content-Type': 'application/json' } }
            );
            
            // Record metrics
            const transitionCheck = check(transitionResponse, {
                'state transition successful': (r) => r.status === 200,
            });
            if (transitionCheck) {
                transitionRate.add(1);
            } else {
                errorRate.add(1);
            }
        }
    }
    
    // Random delay between operations (100ms - 1s)
    sleep(Math.random() * 0.9 + 0.1);
}

export function teardown(data) {
    // Cleanup test tasks
    data.taskIds.forEach(taskId => {
        http.del(`${BASE_URL}/tasks/graph/${taskId}`);
    });
}
