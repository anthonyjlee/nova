<script lang="ts">
  import { userStore } from '$lib/stores/user';
  import { userService } from '$lib/services/user';

  let preferences = {
    theme: $userStore.user?.preferences.theme || 'dark',
    taskFormat: $userStore.user?.preferences.taskFormat || 'default',
    communicationStyle: $userStore.user?.preferences.communicationStyle || 'balanced',
    interfaceMode: $userStore.user?.preferences.interfaceMode || 'standard',
    notifications: $userStore.user?.preferences.notifications || false,
    autoApprove: $userStore.user?.preferences.autoApprove || false
  };

  let saving = false;

  async function handleSubmit() {
    if (!$userStore.user) return;
    
    saving = true;
    try {
      await userService.updatePreferences(preferences);
    } catch (error) {
      console.error('Failed to update preferences:', error);
    } finally {
      saving = false;
    }
  }
</script>

<div class="p-6">
  <h1 class="text-2xl font-semibold text-[#DCDDDE] mb-6">Preferences</h1>

  <form class="max-w-md space-y-6" on:submit|preventDefault={handleSubmit}>
    <!-- Theme -->
    <div>
      <label class="block text-sm font-medium text-[#DCDDDE] mb-2">Theme</label>
      <div class="space-y-2">
        <label class="flex items-center">
          <input
            type="radio"
            bind:group={preferences.theme}
            value="dark"
            class="text-[#5865F2] focus:ring-[#5865F2]"
          />
          <span class="ml-2 text-[#DCDDDE]">Dark</span>
        </label>
        <label class="flex items-center">
          <input
            type="radio"
            bind:group={preferences.theme}
            value="light"
            class="text-[#5865F2] focus:ring-[#5865F2]"
          />
          <span class="ml-2 text-[#DCDDDE]">Light</span>
        </label>
      </div>
    </div>

    <!-- Task Format -->
    <div>
      <label for="taskFormat" class="block text-sm font-medium text-[#DCDDDE] mb-2">Task Format</label>
      <select
        id="taskFormat"
        bind:value={preferences.taskFormat}
        class="w-full px-3 py-2 bg-[#1A1D21] border border-[#2C2D31] rounded-md text-[#DCDDDE] focus:outline-none focus:border-[#5865F2] focus:ring-1 focus:ring-[#5865F2]"
      >
        <option value="default">Default</option>
        <option value="compact">Compact</option>
        <option value="detailed">Detailed</option>
      </select>
    </div>

    <!-- Communication Style -->
    <div>
      <label for="communicationStyle" class="block text-sm font-medium text-[#DCDDDE] mb-2">Communication Style</label>
      <select
        id="communicationStyle"
        bind:value={preferences.communicationStyle}
        class="w-full px-3 py-2 bg-[#1A1D21] border border-[#2C2D31] rounded-md text-[#DCDDDE] focus:outline-none focus:border-[#5865F2] focus:ring-1 focus:ring-[#5865F2]"
      >
        <option value="direct">Direct</option>
        <option value="detailed">Detailed</option>
        <option value="balanced">Balanced</option>
      </select>
    </div>

    <!-- Interface Mode -->
    <div>
      <label for="interfaceMode" class="block text-sm font-medium text-[#DCDDDE] mb-2">Interface Mode</label>
      <select
        id="interfaceMode"
        bind:value={preferences.interfaceMode}
        class="w-full px-3 py-2 bg-[#1A1D21] border border-[#2C2D31] rounded-md text-[#DCDDDE] focus:outline-none focus:border-[#5865F2] focus:ring-1 focus:ring-[#5865F2]"
      >
        <option value="standard">Standard</option>
        <option value="compact">Compact</option>
        <option value="comfortable">Comfortable</option>
      </select>
    </div>

    <!-- Notifications -->
    <div>
      <label class="flex items-center">
        <input
          type="checkbox"
          bind:checked={preferences.notifications}
          class="text-[#5865F2] focus:ring-[#5865F2] rounded"
        />
        <span class="ml-2 text-[#DCDDDE]">Enable Notifications</span>
      </label>
    </div>

    <!-- Auto Approve -->
    <div>
      <label class="flex items-center">
        <input
          type="checkbox"
          bind:checked={preferences.autoApprove}
          class="text-[#5865F2] focus:ring-[#5865F2] rounded"
        />
        <span class="ml-2 text-[#DCDDDE]">Auto Approve Tasks</span>
      </label>
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
