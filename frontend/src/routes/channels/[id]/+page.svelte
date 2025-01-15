<script lang="ts">
import { page } from '$app/stores';
import Chat from '$lib/components/Chat.svelte';
import Navigation from '$lib/components/layout/Navigation.svelte';

$: channelId = $page.params.id;
</script>

<Chat {channelId}>
  <Navigation slot="left-panel" />
</Chat>
