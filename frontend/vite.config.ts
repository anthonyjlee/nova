import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		host: '0.0.0.0', // Allow external connections
		port: 5173,      // Fixed port
		strictPort: true, // Fail if port is in use
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false
			},
			'/debug': {
				target: 'ws://localhost:8000',
				ws: true,
				changeOrigin: true,
				secure: false
			}
		}
	},
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}']
	}
});
