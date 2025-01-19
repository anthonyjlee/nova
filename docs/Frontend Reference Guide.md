# Frontend Reference Guide

## Technologies

- **Framework**: SvelteKit
- **Styling**: TailwindCSS + Custom CSS
- **Type Safety**: TypeScript
- **Schema Validation**: Zod
- **Testing**: Vitest + Playwright
- **Package Manager**: npm

## Project Structure

```
frontend/
├── src/
│   ├── lib/
│   │   ├── actions/       # Svelte actions (e.g., clickOutside)
│   │   ├── components/    # Reusable components
│   │   ├── schemas/       # Zod schemas for validation
│   │   ├── services/      # API services
│   │   ├── stores/        # Svelte stores
│   │   └── types/         # TypeScript types
│   ├── routes/            # SvelteKit pages
│   ├── app.css           # Global styles
│   ├── app.d.ts          # TypeScript declarations
│   └── app.html          # HTML template
├── static/               # Static assets
└── tests/               # Test files
```

## Key Files

### Configuration
- `svelte.config.js` - SvelteKit configuration
- `tailwind.config.ts` - Tailwind CSS configuration
- `vite.config.ts` - Vite configuration
- `tsconfig.json` - TypeScript configuration

### Core Components
- `src/lib/components/Chat.svelte` - Main chat interface
- `src/lib/components/TaskBoard.svelte` - Task management board
- `src/lib/components/Message.svelte` - Chat message component
- `src/lib/components/MemoryPanel.svelte` - Memory visualization
- `src/lib/components/AgentTeamView.svelte` - Agent team display

### Layout Components
- `src/lib/components/layout/Navigation.svelte` - Main navigation
- `src/lib/components/layout/Header.svelte` - App header
- `src/lib/components/layout/UserMenu.svelte` - User menu
- `src/lib/components/layout/UserSettings.svelte` - Settings panel

## Styling Guide

### Color Scheme

```css
/* Background colors */
--slack-bg-primary: #1A1D21;    /* Main background */
--slack-bg-secondary: #2B2D31;  /* Surface background */
--slack-bg-tertiary: #35373C;   /* Elevated background */
--slack-bg-hover: #35373C;      /* Hover state */

/* Text colors */
--slack-text-primary: #DCDDDE;   /* Primary text */
--slack-text-secondary: #949BA4; /* Secondary text */
--slack-text-muted: #72767D;     /* Muted text */

/* Accent colors */
--slack-accent-primary: #5865F2;  /* Primary accent */
--slack-accent-success: #23A559;  /* Success states */
--slack-accent-error: #F23F43;    /* Error states */
--slack-accent-warning: #F0B232;  /* Warning states */
--slack-accent-info: #1264A3;     /* Info states */

/* Border colors */
--slack-border-primary: #2C2D31;  /* Primary border */
--slack-border-hover: #35373C;    /* Hover border */
```

### Common Components

#### Buttons
```html
<button class="form-button form-button-primary">
  Primary Button
</button>

<button class="form-button form-button-danger">
  Danger Button
</button>
```

#### Form Controls
```html
<select class="form-select">
  <!-- Options -->
</select>

<input type="checkbox" class="form-checkbox">

<div contenteditable class="message-input">
  <!-- Editable content -->
</div>
```

## Schema Validation

We use Zod for runtime type checking and validation. Schemas are defined in `src/lib/schemas/` and correspond to backend Pydantic models.

### Example Schema
```typescript
// src/lib/schemas/task.ts
import { z } from 'zod';

export const TaskSchema = z.object({
  id: z.string(),
  title: z.string(),
  status: z.enum(['pending', 'in_progress', 'completed']),
  priority: z.enum(['low', 'medium', 'high']),
  assignee: z.string().optional(),
  dueDate: z.string().datetime().optional()
});

export type Task = z.infer<typeof TaskSchema>;
```

### Key Schema Files
- `schemas/agent.ts` - Agent types and validation
- `schemas/chat.ts` - Chat message schemas
- `schemas/task.ts` - Task schemas
- `schemas/user.ts` - User and auth schemas
- `schemas/websocket.ts` - WebSocket message schemas
- `schemas/knowledge.ts` - Knowledge graph schemas
- `schemas/memory.ts` - Memory system schemas

## Store Pattern

Stores follow a consistent pattern:

```typescript
// src/lib/stores/example.ts
import { writable } from 'svelte/store';
import type { Example } from '$lib/schemas/example';

interface ExampleState {
  items: Example[];
  loading: boolean;
  error: string | null;
}

function createExampleStore() {
  const { subscribe, set, update } = writable<ExampleState>({
    items: [],
    loading: false,
    error: null
  });

  return {
    subscribe,
    set,
    update,
    // Custom methods...
  };
}

export const exampleStore = createExampleStore();
```

## Service Pattern

Services handle API communication:

```typescript
// src/lib/services/example.ts
import { exampleStore } from '$lib/stores/example';
import type { Example } from '$lib/schemas/example';

class ExampleService {
  async fetch(): Promise<void> {
    try {
      exampleStore.setLoading(true);
      const response = await fetch('/api/example');
      const data = await response.json();
      exampleStore.setData(data);
    } catch (error) {
      exampleStore.setError(error instanceof Error ? error.message : 'Unknown error');
    }
  }
}

export const exampleService = new ExampleService();
```

## WebSocket Integration

WebSocket communication is handled through the WebSocket service and store:

```typescript
// src/lib/services/websocket.ts
import { WebSocketMessage } from '$lib/schemas/websocket';

export class WebSocket {
  connect(): Promise<void>;
  send(message: WebSocketMessage): void;
  subscribe(channel: string): void;
  unsubscribe(channel: string): void;
}
```

## Testing

- Unit Tests: `src/test/unit/`
- Integration Tests: `src/test/integration/`
- E2E Tests: `e2e/`

Run tests with:
```bash
# Unit and integration tests
npm run test

# E2E tests
npm run test:e2e
