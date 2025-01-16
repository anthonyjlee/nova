<script lang="ts">
import '../app.css';
import Layout from '$lib/components/layout/Layout.svelte';
import ErrorBoundary from '$lib/components/shared/ErrorBoundary.svelte';
import DebugPanel from '$lib/components/DebugPanel.svelte';
</script>

<ErrorBoundary>
  <Layout>
    <slot />
  </Layout>
  <DebugPanel />
</ErrorBoundary>
