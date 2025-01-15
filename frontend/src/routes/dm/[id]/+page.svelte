<script lang="ts">
import { page } from '$app/stores';
import Chat from '$lib/components/Chat.svelte';
import Navigation from '$lib/components/layout/Navigation.svelte';

$: agentId = $page.params.id;
</script>

<Chat channelId={agentId}>
  <Navigation slot="left-panel" />
</Chat>
