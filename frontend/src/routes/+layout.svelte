<script lang="ts">
  import '../app.css';
  import Navigation from '$lib/components/layout/Navigation.svelte';
  import { userService } from '$lib/services/user';
  import { onMount } from 'svelte';

  onMount(async () => {
    try {
      await userService.loadUser();
    } catch (error) {
      console.error('Failed to load user:', error);
    }
  });
</script>

<div class="flex h-screen bg-[#1A1D21]">
  <!-- Navigation -->
  <Navigation />

  <!-- Main Content -->
  <main class="flex-1 flex flex-col overflow-hidden">
    <!-- Page Content -->
    <div class="flex-1 overflow-hidden">
      <slot />
    </div>
  </main>
</div>
