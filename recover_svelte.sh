#!/bin/bash

# Create results directory on Desktop
RESULTS_DIR=~/Desktop/svelte_recovery_results
mkdir -p "$RESULTS_DIR"

# Store results in a file
RESULTS_FILE="$RESULTS_DIR/recovery_status.txt"

# Write findings
cat > "$RESULTS_FILE" << EOL
Svelte/TypeScript Files Recovery Status
=====================================
Last Check: $(date)

Found Files (1):
---------------
1. frontend/src/lib/types/chat.ts
   - Last modified: $(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "frontend/src/lib/types/chat.ts")
   - Contains: TypeScript interfaces for Message, Thread, ThreadParticipant, WebSocketMessage, ThreadMessage
   - No previous versions found in VSCode history

Missing Files (10):
----------------
Components:
1. frontend/src/lib/components/GraphPanel.svelte
2. frontend/src/lib/components/AgentTeamView.svelte
3. frontend/src/lib/components/AgentDetailsPanel.svelte
4. frontend/src/lib/components/TaskDetails.svelte
5. frontend/src/lib/components/TaskModal.svelte

Services:
6. frontend/src/lib/services/chat.ts
7. frontend/src/lib/services/tasks.ts

Types:
8. frontend/src/lib/types/websocket.ts

Utils:
9. frontend/src/lib/utils/validation.ts
10. frontend/src/lib/utils/task.ts

Note: No history versions were found for any of these files in VSCode's history directory.
EOL

# Print simple status to console
echo "Recovery status report saved to: $RESULTS_FILE"
