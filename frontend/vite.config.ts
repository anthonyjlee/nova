import { defineConfig } from 'vitest/config';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		proxy: {
			'/api': {
				target: 'http://localhost:8001',
				changeOrigin: true,
				secure: false
			},
			'/api/ws': {
				target: 'ws://localhost:8001',
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
