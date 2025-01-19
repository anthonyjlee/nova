<script lang="ts">
  import { page } from '$app/stores';
</script>

<div class="flex h-full bg-[#1A1D21]">
  <!-- Settings Navigation -->
  <div class="w-60 border-r border-[#2C2D31] bg-[#2B2D31]">
    <div class="px-4 py-3">
      <h2 class="text-lg font-semibold text-[#DCDDDE]">User Settings</h2>
    </div>
    <nav class="px-2 py-2 space-y-1">
      <a
        href="/settings/profile"
        class="flex items-center px-2 py-1.5 rounded-md text-[14px] font-medium hover:bg-[#35373C] transition-colors"
        class:text-white={$page.url.pathname === '/settings/profile'}
        class:bg-[#35373C]={$page.url.pathname === '/settings/profile'}
      >
        Profile
      </a>
      <a
        href="/settings/preferences"
        class="flex items-center px-2 py-1.5 rounded-md text-[14px] font-medium hover:bg-[#35373C] transition-colors"
        class:text-white={$page.url.pathname === '/settings/preferences'}
        class:bg-[#35373C]={$page.url.pathname === '/settings/preferences'}
      >
        Preferences
      </a>
      <a
        href="/settings/status"
        class="flex items-center px-2 py-1.5 rounded-md text-[14px] font-medium hover:bg-[#35373C] transition-colors"
        class:text-white={$page.url.pathname === '/settings/status'}
        class:bg-[#35373C]={$page.url.pathname === '/settings/status'}
      >
        Status
      </a>
    </nav>
  </div>

  <!-- Content -->
  <div class="flex-1 overflow-y-auto">
    <slot />
  </div>
</div>
