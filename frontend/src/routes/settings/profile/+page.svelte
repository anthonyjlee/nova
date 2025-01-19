<script lang="ts">
  import { userStore } from '$lib/stores/user';
  import { userService } from '$lib/services/user';

  let name = $userStore.user?.name || '';
  let email = $userStore.user?.email || '';
  let saving = false;

  async function handleSubmit() {
    if (!$userStore.user) return;
    
    saving = true;
    try {
      await userService.updateProfile({ name, email });
    } catch (error) {
      console.error('Failed to update profile:', error);
    } finally {
      saving = false;
    }
  }
</script>

<div class="p-6">
  <h1 class="text-2xl font-semibold text-[#DCDDDE] mb-6">Profile Settings</h1>

  <form class="max-w-md space-y-4" on:submit|preventDefault={handleSubmit}>
    <div>
      <label for="name" class="block text-sm font-medium text-[#DCDDDE] mb-1">Display Name</label>
      <input
        id="name"
        type="text"
        bind:value={name}
        class="w-full px-3 py-2 bg-[#1A1D21] border border-[#2C2D31] rounded-md text-[#DCDDDE] focus:outline-none focus:border-[#5865F2] focus:ring-1 focus:ring-[#5865F2]"
      />
    </div>

    <div>
      <label for="email" class="block text-sm font-medium text-[#DCDDDE] mb-1">Email</label>
      <input
        id="email"
        type="email"
        bind:value={email}
        class="w-full px-3 py-2 bg-[#1A1D21] border border-[#2C2D31] rounded-md text-[#DCDDDE] focus:outline-none focus:border-[#5865F2] focus:ring-1 focus:ring-[#5865F2]"
      />
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
