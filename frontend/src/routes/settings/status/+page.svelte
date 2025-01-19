<script lang="ts">
  import { userStore } from '$lib/stores/user';
  import { userService } from '$lib/services/user';
  import type { UserStatus } from '$lib/schemas/user';

  const statusOptions: Array<{
    value: UserStatus;
    label: string;
    color: string;
  }> = [
    { value: 'online', label: 'Online', color: '#23A559' },
    { value: 'idle', label: 'Idle', color: '#F0B232' },
    { value: 'dnd', label: 'Do Not Disturb', color: '#F23F43' },
    { value: 'invisible', label: 'Invisible', color: '#80848E' }
  ];

  let selectedStatus: UserStatus = $userStore.user?.status || 'online';
  let customStatus = $userStore.user?.customStatus || '';
  let saving = false;

  async function handleSubmit() {
    if (!$userStore.user) return;
    
    saving = true;
    try {
      await userService.updateStatus(selectedStatus, customStatus);
    } catch (error) {
      console.error('Failed to update status:', error);
    } finally {
      saving = false;
    }
  }
</script>

<div class="p-6">
  <h1 class="text-2xl font-semibold text-[#DCDDDE] mb-6">Set Status</h1>

  <form class="max-w-md space-y-6" on:submit|preventDefault={handleSubmit}>
    <!-- Status Options -->
    <div class="space-y-3">
      {#each statusOptions as option}
        <label class="flex items-center p-2 rounded hover:bg-[#35373C] cursor-pointer transition-colors">
          <input
            type="radio"
            bind:group={selectedStatus}
            value={option.value}
            class="text-[#5865F2] focus:ring-[#5865F2]"
          />
          <span class="ml-3 flex items-center">
            <span class="w-2.5 h-2.5 rounded-full" style="background-color: {option.color}"></span>
            <span class="ml-2 text-[#DCDDDE]">{option.label}</span>
          </span>
        </label>
      {/each}
    </div>

    <!-- Custom Status -->
    <div>
      <label for="customStatus" class="block text-sm font-medium text-[#DCDDDE] mb-2">Custom Status</label>
      <input
        id="customStatus"
        type="text"
        bind:value={customStatus}
        placeholder="What's on your mind?"
        maxlength="50"
        class="w-full px-3 py-2 bg-[#1A1D21] border border-[#2C2D31] rounded-md text-[#DCDDDE] placeholder-[#72767D] focus:outline-none focus:border-[#5865F2] focus:ring-1 focus:ring-[#5865F2]"
      />
      {#if customStatus}
        <p class="mt-1 text-xs text-[#949BA4]">{customStatus.length}/50</p>
      {/if}
    </div>

    <button
      type="submit"
      disabled={saving}
      class="px-4 py-2 bg-[#5865F2] text-white rounded-md font-medium hover:bg-[#4752C4] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#5865F2] disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {saving ? 'Saving...' : 'Save Changes'}
    </button>
  </form>
</div>
