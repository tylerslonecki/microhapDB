<template>
  <div class="user-management">
    <div class="surface-card p-4 border-round shadow-2">
      <div class="text-3xl font-medium text-900 mb-4">User Management</div>
      
      <!-- Access Information -->
      <div class="card mb-4">
        <div class="p-4 surface-100 border-round">
          <div class="flex align-items-center">
            <i class="pi pi-info-circle mr-3 text-2xl text-blue-500"></i>
            <div>
              <h3 class="text-xl font-medium text-900 mb-1">Private User Access</h3>
              <p class="m-0 text-600">
                As a private user, you can manage your collaborators and access enhanced features. 
                You do not have access to admin functions like creating users or accessing system data uploads.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Personal Collaborator Management Section -->
      <div class="card">
        <h3 class="text-xl font-medium text-900 mb-3">My Collaborators</h3>
        <ProgressSpinner v-if="loadingPersonalCollaborators" class="w-4rem h-4rem" />
        <div v-else-if="personalCollaborators.length === 0" class="surface-200 border-round p-4">
          <i class="pi pi-info-circle mr-2"></i>
          You don't have any collaborators yet.
        </div>
        <div v-else>
          <ul class="list-none p-0 m-0">
            <li v-for="collaborator in personalCollaborators" :key="collaborator.id" 
                class="flex align-items-center justify-content-between p-3 border-bottom-1 surface-border">
              <div>
                <span class="font-medium text-900">{{ collaborator.full_name }}</span>
                <div class="text-600">ORCID: {{ collaborator.orcid }}</div>
                <Tag 
                  :value="collaborator.role" 
                  :severity="getRoleSeverity(collaborator.role)"
                  class="mt-1"
                />
              </div>
              <Button 
                icon="pi pi-trash" 
                class="p-button-rounded p-button-danger p-button-text"
                @click="removePersonalCollaborator(collaborator.id)"
                v-tooltip.left="'Remove Collaborator'"
              />
            </li>
          </ul>
        </div>

        <div class="mt-4">
          <h4 class="text-lg font-medium text-900 mb-3">Add Collaborator</h4>
          <div v-if="availablePersonalUsers.length === 0" class="surface-200 border-round p-4">
            <i class="pi pi-info-circle mr-2"></i>
            No available users to add as collaborators.
          </div>
          <div v-else class="flex gap-2">
            <Dropdown
              v-model="selectedPersonalUserId"
              :options="availablePersonalUsers"
              optionLabel="full_name"
              optionValue="id"
              placeholder="Select a user..."
              class="w-full"
            >
              <template #option="slotProps">
                <div>
                  <div class="font-medium">{{ slotProps.option.full_name }}</div>
                  <div class="text-sm text-600">{{ slotProps.option.orcid }}</div>
                  <Tag 
                    :value="slotProps.option.role" 
                    :severity="getRoleSeverity(slotProps.option.role)"
                    class="mt-1"
                  />
                </div>
              </template>
            </Dropdown>
            <Button 
              label="Add" 
              icon="pi pi-plus"
              @click="addPersonalCollaborator"
              :disabled="!selectedPersonalUserId"
              class="p-button-success"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Toast for notifications -->
    <Toast />
  </div>
</template>

<script>
import { useToast } from 'primevue/usetoast';
import axios from 'axios';
import { mapState, mapGetters } from 'vuex';

export default {
  name: 'UserManagement',
  setup() {
    const toast = useToast();
    return { toast };
  },
  data() {
    return {
      personalCollaborators: [],
      availablePersonalUsers: [],
      selectedPersonalUserId: '',
      loadingPersonalCollaborators: true,
      error: null
    };
  },
  computed: {
    ...mapState('auth', ['user']),
    ...mapGetters('auth', ['userRole', 'isAdmin', 'canAccessPrivateData'])
  },
  methods: {
    async loadPersonalCollaborators() {
      try {
        const response = await axios.get('/auth/users/me/collaborators');
        this.personalCollaborators = response.data;
      } catch (error) {
        console.error('Error loading personal collaborators:', error);
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load collaborators',
          life: 3000
        });
      }
    },
    async loadAvailablePersonalUsers() {
      try {
        const response = await axios.get('/auth/users');
        const collaboratorIds = this.personalCollaborators.map(c => c.id);
        
        this.availablePersonalUsers = response.data.filter(user => {
          return user.id !== this.user?.id && !collaboratorIds.includes(user.id);
        });
      } catch (error) {
        console.error('Error loading available users for personal collaborators:', error);
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load available users',
          life: 3000
        });
      }
    },
    async addPersonalCollaborator() {
      if (!this.selectedPersonalUserId) return;
      
      try {
        await axios.post(`/auth/users/me/collaborators/${this.selectedPersonalUserId}`);
        this.toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Collaborator added successfully',
          life: 3000
        });
        await this.loadPersonalCollaborators();
        await this.loadAvailablePersonalUsers();
        this.selectedPersonalUserId = '';
      } catch (error) {
        console.error('Error adding personal collaborator:', error);
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.response?.data?.detail || 'Failed to add collaborator',
          life: 3000
        });
      }
    },
    async removePersonalCollaborator(collaboratorId) {
      try {
        await axios.delete(`/auth/users/me/collaborators/${collaboratorId}`);
        this.toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Collaborator removed successfully',
          life: 3000
        });
        await this.loadPersonalCollaborators();
        await this.loadAvailablePersonalUsers();
      } catch (error) {
        console.error('Error removing personal collaborator:', error);
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.response?.data?.detail || 'Failed to remove collaborator',
          life: 3000
        });
      }
    },
    getRoleSeverity(role) {
      switch (role) {
        case 'admin':
          return 'danger';
        case 'private_user':
          return 'warning';
        case 'collaborator':
          return 'info';
        default:
          return 'success';
      }
    }
  },
  async created() {
    try {
      // Check if user has proper access
      if (this.userRole !== 'private_user') {
        this.toast.add({
          severity: 'error',
          summary: 'Access Denied',
          detail: 'This page is only accessible to private users.',
          life: 5000
        });
        this.$router.push('/');
        return;
      }

      await Promise.all([
        this.loadPersonalCollaborators(),
        this.loadAvailablePersonalUsers()
      ]);
    } catch (error) {
      console.error('Error in UserManagement created hook:', error);
      this.toast.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to initialize user management. Please try refreshing the page.',
        life: 5000
      });
    } finally {
      this.loadingPersonalCollaborators = false;
    }
  }
};
</script>

<style scoped>
.user-management {
  max-width: 1000px;
  margin: 0 auto;
  padding: 2rem;
}

@media (max-width: 768px) {
  .user-management {
    padding: 1rem;
  }
}
</style> 