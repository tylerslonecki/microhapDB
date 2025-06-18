<template>
  <div class="user-management">
    <div class="surface-card p-4 border-round shadow-2">
      <div class="text-3xl font-medium text-900 mb-4">Privacy & Collaborators</div>
      
      <!-- Privacy Information -->
      <div class="card mb-4">
        <div class="p-4 surface-100 border-round">
          <div class="flex align-items-center mb-3">
            <i class="pi pi-shield mr-3 text-2xl text-blue-500"></i>
            <h3 class="text-xl font-medium text-900 mb-0">Data Privacy & Sharing Classifications</h3>
          </div>
          <div class="grid">
            <div class="col-12 md:col-4 mb-3">
              <div class="card h-full p-3 surface-50">
                <div class="flex align-items-center mb-2">
                  <i class="pi pi-eye text-green-600 mr-2"></i>
                  <h4 class="text-lg font-medium text-900 mb-0">Public Data</h4>
                </div>
                <p class="text-600 text-sm mb-2">Available to all users and researchers:</p>
                <ul class="text-600 text-sm mb-0 pl-3">
                  <li><strong>AlleleIDs</strong> - Unique identifiers</li>
                  <li><strong>Allele Sequences</strong> - Genetic sequences</li>
                  <li><strong>Info field</strong> - General information</li>
                  <li><strong>Institution</strong> - Contributing organizations</li>
                  <li><strong>Project</strong> - Research project names</li>
                  <li>Database reports and statistics</li>
                  <li>General query results</li>
                </ul>
              </div>
            </div>
            <div class="col-12 md:col-4 mb-3">
              <div class="card h-full p-3 surface-50">
                <div class="flex align-items-center mb-2">
                  <i class="pi pi-users text-blue-600 mr-2"></i>
                  <h4 class="text-lg font-medium text-900 mb-0">Shared with Collaborators</h4>
                </div>
                <p class="text-600 text-sm mb-2">Visible to you and your collaborators only:</p>
                <ul class="text-600 text-sm mb-0 pl-3">
                  <li><strong>Program</strong> - Internal program classifications</li>
                  <li>Your private data uploads</li>
                  <li>Collaborative research projects</li>
                  <li>Shared analysis results</li>
                  <li>Private datasets you've shared</li>
                  <li>Research notes and annotations</li>
                </ul>
              </div>
            </div>
            <div class="col-12 md:col-4 mb-3">
              <div class="card h-full p-3 surface-50">
                <div class="flex align-items-center mb-2">
                  <i class="pi pi-lock text-red-600 mr-2"></i>
                  <h4 class="text-lg font-medium text-900 mb-0">Always Private</h4>
                </div>
                <p class="text-600 text-sm mb-2">Visible only to you (and administrators):</p>
                <ul class="text-600 text-sm mb-0 pl-3">
                  <li><strong>Associated traits</strong> - Phenotypic data</li>
                  <li><strong>Accessions</strong> - Sample identifiers</li>
                  <li>Your account details</li>
                  <li>Personal settings and preferences</li>
                  <li>Upload history and metadata</li>
                  <li>Collaboration relationships</li>
                </ul>
                <small class="text-red-500 block mt-2">*System administrators can view all data for database management purposes</small>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Access Information -->
      <div class="card mb-4">
        <div class="p-4 surface-200 border-round">
          <div class="flex align-items-center">
            <i class="pi pi-info-circle mr-3 text-2xl text-orange-500"></i>
            <div>
              <h3 class="text-xl font-medium text-900 mb-1">Private User Access</h3>
              <p class="m-0 text-600">
                As a private user, you can manage collaborators to share your private data and collaborate on research. 
                Adding someone as a collaborator gives them access to your private datasets and uploads, but your personal 
                account information remains private. Only system administrators can view all user data for system management purposes.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Personal Collaborator Management Section -->
      <div class="card">
        <div class="flex align-items-center justify-content-between mb-3">
          <h3 class="text-xl font-medium text-900 mb-0">My Collaborators</h3>
          <Tag :value="`${personalCollaborators.length} Active`" severity="info" />
        </div>
        
        <div class="p-3 surface-50 border-round mb-4">
          <div class="flex align-items-start">
            <i class="pi pi-info-circle text-blue-500 mr-2 mt-1"></i>
            <div>
              <p class="text-600 text-sm mb-2">
                <strong>How Collaboration Works:</strong> When you add someone as a collaborator, they gain access to:
              </p>
              <ul class="text-600 text-sm m-0 pl-3">
                <li>Your private data uploads and datasets</li>
                <li>Shared research projects and analysis results</li>
                <li>Ability to view and work with your private database entries</li>
              </ul>
              <p class="text-600 text-sm mt-2 mb-0">
                <strong>Note:</strong> Your personal account information and settings remain private. 
                You can remove collaborators at any time to revoke their access.
              </p>
            </div>
          </div>
        </div>

        <ProgressSpinner v-if="loadingPersonalCollaborators" class="w-4rem h-4rem" />
        <div v-else-if="personalCollaborators.length === 0" class="surface-200 border-round p-4">
          <i class="pi pi-users mr-2"></i>
          You don't have any collaborators yet. Add collaborators below to share your private data.
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
                v-tooltip.left="'Remove Collaborator (Revokes access to your private data)'"
              />
            </li>
          </ul>
        </div>

        <div class="mt-4">
          <h4 class="text-lg font-medium text-900 mb-3">Add New Collaborator</h4>
          <div v-if="availablePersonalUsers.length === 0" class="surface-200 border-round p-4">
            <i class="pi pi-info-circle mr-2"></i>
            No available users to add as collaborators. All existing users are either already collaborators or have admin access.
          </div>
          <div v-else>
            <p class="text-600 text-sm mb-3">
              Select a user to grant them access to your private data and research projects:
            </p>
            <div class="flex gap-2">
              <Dropdown
                v-model="selectedPersonalUserId"
                :options="availablePersonalUsers"
                optionLabel="full_name"
                optionValue="id"
                placeholder="Select a user to add as collaborator..."
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
                label="Add Collaborator" 
                icon="pi pi-plus"
                @click="addPersonalCollaborator"
                :disabled="!selectedPersonalUserId"
                class="p-button-success"
              />
            </div>
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
  name: 'PrivacyCollaborators',
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
          detail: 'This page is only accessible to private users for managing privacy settings and collaborators.',
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
      console.error('Error in PrivacyCollaborators created hook:', error);
      this.toast.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to initialize privacy and collaboration settings. Please try refreshing the page.',
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