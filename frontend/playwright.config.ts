import type { PlaywrightTestConfig } from '@playwright/test';

const config: PlaywrightTestConfig = {
    testDir: './e2e',
    timeout: 60000,
    expect: {
        timeout: 10000
    },
    fullyParallel: true,
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: process.env.CI ? 1 : undefined,
    reporter: 'html',
    use: {
        actionTimeout: 0,
        baseURL: 'http://localhost:5173',
        trace: 'on-first-retry',
        video: 'on-first-retry',
        screenshot: 'only-on-failure'
    },
    projects: [
        {
            name: 'chromium',
            use: {
                browserName: 'chromium'
            }
        },
        {
            name: 'firefox',
            use: {
                browserName: 'firefox'
            }
        },
        {
            name: 'webkit',
            use: {
                browserName: 'webkit'
            }
        }
    ]
};

export default config;
