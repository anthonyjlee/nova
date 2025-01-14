<script lang="ts">
import '../app.css';
import Layout from '$lib/components/layout/Layout.svelte';
import ErrorBoundary from '$lib/components/shared/ErrorBoundary.svelte';
</script>

<ErrorBoundary>
  <Layout>
    <slot />
  </Layout>
</ErrorBoundary>
