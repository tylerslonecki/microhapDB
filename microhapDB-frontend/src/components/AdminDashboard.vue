<template>
  <div class="admin-dashboard">
    <div class="surface-card p-4 border-round shadow-2">
      <div class="text-3xl font-medium text-900 mb-4">Admin Dashboard</div>
      
      <!-- Admin-only sections -->
      <div v-if="isAdmin">
        <!-- Add New User Section -->
        <div class="card mb-4">
          <h3 class="text-xl font-medium text-900 mb-3">Add New User</h3>
          <div class="formgrid grid">
            <div class="field col-12 md:col-4">
              <label for="fullName" class="block text-900 font-medium mb-2">Full Name</label>
              <InputText 
                id="fullName"
                v-model="newUserFullName" 
                placeholder="Enter full name"
                class="w-full" 
                :class="{ 'p-invalid': fullNameError }"
              />
              <small class="p-error" v-if="fullNameError">{{ fullNameError }}</small>
            </div>
            <div class="field col-12 md:col-4">
              <label for="orcid" class="block text-900 font-medium mb-2">ORCID</label>
              <InputText 
                id="orcid"
                v-model="newUserOrcid" 
                placeholder="Enter ORCID (e.g., 0000-0000-0000-0000)"
                class="w-full" 
                :class="{ 'p-invalid': orcidError }"
              />
              <small class="p-error" v-if="orcidError">{{ orcidError }}</small>
            </div>
            <div class="field col-12 md:col-3">
              <label for="role" class="block text-900 font-medium mb-2">Role</label>
              <Dropdown
                id="role"
                v-model="newUserRole"
                :options="roleOptions"
                optionLabel="label"
                optionValue="value"
                placeholder="Select Role"
                class="w-full"
              />
            </div>
            <div class="field col-12 md:col-1 flex align-items-end">
              <Button 
                label="Add" 
                icon="pi pi-user-plus"
                @click="addNewUser"
                :loading="addingUser"
                class="p-button-success w-full"
              />
            </div>
          </div>
        </div>
        
        <!-- Bulk User Creation Section -->
        <div class="card mb-4">
          <h3 class="text-xl font-medium text-900 mb-3">Bulk User Creation</h3>
          <div class="mb-3">
            <p class="text-600 mb-2">
              Create multiple users at once by providing CSV data. Format: Full Name, ORCID, Role
            </p>
            <small class="text-500">
              Example: <code>John Doe, 0000-0000-0000-0001, private_user</code>
            </small>
          </div>
          <div class="field">
            <label for="bulkUserData" class="block text-900 font-medium mb-2">User Data (CSV Format)</label>
            <Textarea 
              id="bulkUserData"
              v-model="bulkUserData" 
              rows="5" 
              class="w-full"
              placeholder="John Doe, 0000-0000-0000-0001, private_user
Jane Smith, 0000-0000-0000-0002, collaborator
Admin User, 0000-0000-0000-0003, admin"
            />
          </div>
          <div class="flex gap-2">
            <Button 
              label="Create Users" 
              icon="pi pi-users"
              @click="bulkCreateUsers"
              :loading="bulkCreating"
              class="p-button-info"
              :disabled="!bulkUserData.trim()"
            />
            <Button 
              label="Clear" 
              icon="pi pi-times"
              @click="bulkUserData = ''"
              class="p-button-secondary"
              :disabled="!bulkUserData.trim()"
            />
          </div>
          <div v-if="bulkResults.length > 0" class="mt-4">
            <h4 class="text-lg font-medium text-900 mb-2">Bulk Creation Results:</h4>
            <div class="max-h-20rem overflow-auto">
              <div 
                v-for="(result, index) in bulkResults" 
                :key="index"
                class="flex align-items-center justify-content-between p-2 border-bottom-1 surface-border"
                :class="result.success ? 'text-green-600' : 'text-red-600'"
              >
                <span>{{ result.name }} ({{ result.orcid }})</span>
                <Tag 
                  :value="result.success ? 'Success' : 'Failed'" 
                  :severity="result.success ? 'success' : 'danger'"
                />
              </div>
            </div>
          </div>
        </div>
        
        <!-- User Management Section -->
        <div class="card mb-4">
          <h3 class="text-xl font-medium text-900 mb-3">User Management</h3>
          <DataTable 
            :value="users" 
            :paginator="true" 
            :rows="10"
            :rowsPerPageOptions="[5, 10, 20]"
            stripedRows
            v-model:filters="filters"
            filterDisplay="row"
            dataKey="id"
            responsiveLayout="scroll"
            class="p-datatable-sm"
            :loading="!users.length"
          >
            <Column 
              field="full_name" 
              header="Name"
              :sortable="true"
              style="min-width: 200px"
            >
              <template #filter="{ filterModel, filterCallback }">
                <InputText
                  v-model="filterModel.value"
                  type="text"
                  @input="filterCallback()"
                  class="p-column-filter w-full"
                  placeholder="Search name..."
                />
              </template>
            </Column>
            <Column 
              field="orcid" 
              header="ORCID"
              :sortable="true"
              style="min-width: 150px"
            >
              <template #filter="{ filterModel, filterCallback }">
                <InputText
                  v-model="filterModel.value"
                  type="text"
                  @input="filterCallback()"
                  class="p-column-filter w-full"
                  placeholder="Search ORCID..."
                />
              </template>
            </Column>
            <Column 
              field="role" 
              header="Role"
              :sortable="true"
              style="min-width: 150px"
            >
              <template #body="slotProps">
                <div class="flex align-items-center gap-2">
                  <Tag 
                    :value="slotProps.data.role" 
                    :severity="getRoleSeverity(slotProps.data.role)"
                  />
                  <Dropdown
                    v-model="slotProps.data.role"
                    :options="roleOptions"
                    optionLabel="label"
                    optionValue="value"
                    @change="updateUserRole(slotProps.data)"
                    class="ml-2"
                  />
                </div>
              </template>
              <template #filter="{ filterModel, filterCallback }">
                <Dropdown
                  v-model="filterModel.value"
                  :options="roleOptions"
                  optionLabel="label"
                  optionValue="value"
                  @change="filterCallback()"
                  class="p-column-filter w-full"
                  placeholder="Select Role"
                />
              </template>
            </Column>
            <Column 
              field="is_active" 
              header="Status"
              :sortable="true"
              style="min-width: 100px"
            >
              <template #body="slotProps">
                <Tag 
                  :value="slotProps.data.is_active ? 'Active' : 'Inactive'" 
                  :severity="slotProps.data.is_active ? 'success' : 'danger'"
                />
              </template>
            </Column>
            <Column 
              header="Actions" 
              style="min-width: 150px"
              :exportable="false"
            >
              <template #body="slotProps">
                <div class="flex gap-1">
                  <Button 
                    icon="pi pi-users"
                    class="p-button-rounded p-button-info p-button-text"
                    @click="showCollaboratorModal(slotProps.data)"
                    v-tooltip.top="'Manage Collaborators'"
                  />
                  <Button 
                    icon="pi pi-trash"
                    class="p-button-rounded p-button-danger p-button-text"
                    @click="confirmDeleteUser(slotProps.data)"
                    v-tooltip.top="'Delete User'"
                    :disabled="slotProps.data.id === user?.id"
                  />
                </div>
              </template>
            </Column>
          </DataTable>
        </div>
      </div>
      
      <!-- Non-admin message -->
      <div v-if="!isAdmin" class="card mb-4">
        <div class="p-4 surface-200 border-round">
          <div class="flex align-items-center">
            <i class="pi pi-lock mr-3 text-2xl text-yellow-500"></i>
            <div>
              <h3 class="text-xl font-medium text-900 mb-1">Admin Access Required</h3>
              <p class="m-0 text-600">
                You need admin privileges to access user management features. 
                You can still manage your personal collaborators below.
              </p>
            </div>
          </div>
        </div>
      </div>

      <!-- Personal Collaborator Management Section -->
      <div v-if="userRole === 'admin' || userRole === 'private_user'" class="card">
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
            />
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

    <!-- Collaborator Management Modal -->
    <Dialog 
      v-model:visible="showModal" 
      :header="`Manage Collaborators for ${selectedUser?.full_name || ''}`"
      :modal="true"
      :style="{ width: '50vw' }"
      class="p-fluid"
    >
      <div class="mb-4">
        <h4 class="text-lg font-medium text-900 mb-3">Current Collaborators</h4>
        <div v-if="currentCollaborators.length === 0" class="surface-200 border-round p-4">
          <i class="pi pi-info-circle mr-2"></i>
          No collaborators yet
        </div>
        <ul v-else class="list-none p-0 m-0">
          <li v-for="collaborator in currentCollaborators" 
              :key="collaborator.id"
              class="flex align-items-center justify-content-between p-3 border-bottom-1 surface-border">
            <span class="font-medium">{{ collaborator.full_name }}</span>
            <Button 
              icon="pi pi-times"
              class="p-button-rounded p-button-danger p-button-text"
              @click="removeCollaborator(collaborator)"
              v-tooltip.left="'Remove Collaborator'"
            />
          </li>
        </ul>
      </div>
      <div class="add-collaborator">
        <h4 class="text-lg font-medium text-900 mb-3">Add Collaborator</h4>
        <div class="flex gap-2">
          <Dropdown
            v-model="newCollaboratorId"
            :options="availableUsers"
            optionLabel="full_name"
            optionValue="id"
            placeholder="Select a user..."
            class="w-full"
          />
          <Button 
            icon="pi pi-plus"
            label="Add"
            @click="addCollaborator"
            :disabled="!newCollaboratorId"
            class="p-button-success"
          />
        </div>
      </div>
      <template #footer>
        <Button 
          label="Close" 
          icon="pi pi-times" 
          @click="closeModal" 
          class="p-button-text"
        />
      </template>
    </Dialog>

    <!-- Toast for notifications -->
    <Toast />
    
    <!-- Delete User Confirmation Dialog -->
    <Dialog 
      v-model:visible="showDeleteDialog" 
      header="Confirm Delete User"
      :modal="true"
      :style="{ width: '450px' }"
      class="p-fluid"
    >
      <div class="flex align-items-center mb-4">
        <i class="pi pi-exclamation-triangle mr-3 text-orange-500" style="font-size: 2rem"></i>
        <div>
          <p class="mb-2">Are you sure you want to delete this user?</p>
          <p class="font-medium text-900">{{ userToDelete?.full_name }}</p>
          <p class="text-600">ORCID: {{ userToDelete?.orcid }}</p>
          <p class="text-red-500 mt-2">
            <strong>Warning:</strong> This action cannot be undone and will remove all associated data.
          </p>
        </div>
      </div>
      <template #footer>
        <Button 
          label="Cancel" 
          icon="pi pi-times" 
          @click="showDeleteDialog = false" 
          class="p-button-text"
        />
        <Button 
          label="Delete" 
          icon="pi pi-trash" 
          @click="deleteUser" 
          class="p-button-danger"
          :loading="deletingUser"
        />
      </template>
    </Dialog>
  </div>
</template>

<script>
import { useToast } from 'primevue/usetoast';
import { FilterMatchMode } from 'primevue/api';
import axios from 'axios';
import { mapState, mapGetters } from 'vuex';

export default {
  name: 'AdminDashboard',
  setup() {
    const toast = useToast();
    return { toast };
  },
  data() {
    return {
      users: [],
      showModal: false,
      selectedUser: null,
      currentCollaborators: [],
      availableUsers: [],
      newCollaboratorId: null,
      newUserFullName: '',
      newUserOrcid: '',
      newUserRole: null,
      addingUser: false,
      fullNameError: '',
      orcidError: '',
      roleOptions: [
        { label: 'Admin', value: 'admin' },
        { label: 'Private User', value: 'private_user' },
        { label: 'Collaborator', value: 'collaborator' },
        { label: 'Public', value: 'public' }
      ],
      filters: {
        full_name: { value: null, matchMode: FilterMatchMode.CONTAINS },
        orcid: { value: null, matchMode: FilterMatchMode.CONTAINS },
        role: { value: null, matchMode: FilterMatchMode.EQUALS }
      },
      personalCollaborators: [],
      availablePersonalUsers: [],
      selectedPersonalUserId: '',
      loadingPersonalCollaborators: true,
      error: null,
      bulkUserData: '',
      bulkCreating: false,
      bulkResults: [],
      showDeleteDialog: false,
      userToDelete: null,
      deletingUser: false
    };
  },
  computed: {
    ...mapState('auth', ['user']),
    ...mapGetters('auth', ['userRole', 'isAdmin', 'canAccessPrivateData'])
  },
  methods: {
    validateOrcid(orcid) {
      const orcidPattern = /^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$/;
      return orcidPattern.test(orcid);
    },
    async addNewUser() {
      // Reset previous errors
      this.fullNameError = '';
      this.orcidError = '';

      // Validate all fields
      if (!this.newUserFullName.trim()) {
        this.fullNameError = 'Full name is required';
      }

      if (!this.newUserOrcid.trim()) {
        this.orcidError = 'ORCID is required';
      } else if (!this.validateOrcid(this.newUserOrcid)) {
        this.orcidError = 'Invalid ORCID format. Use: 0000-0000-0000-0000';
      }

      if (!this.newUserRole) {
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Please select a role',
          life: 3000
        });
        return;
      }

      // If there are validation errors, don't proceed
      if (this.fullNameError || this.orcidError) {
        return;
      }

      this.addingUser = true;

      try {
        // Create user directly using the new endpoint
        const userData = {
          full_name: this.newUserFullName.trim(),
          orcid: this.newUserOrcid,
          role: this.newUserRole,
          is_active: true
        };

        const response = await axios.post('/auth/admin/users', userData);
        
        this.toast.add({
          severity: 'success',
          summary: 'Success',
          detail: `User "${response.data.full_name}" has been created successfully with role: ${response.data.role}`,
          life: 5000
        });
        
        // Reset form
        this.newUserFullName = '';
        this.newUserOrcid = '';
        this.newUserRole = null;
        
        // Refresh the user list
        await this.loadUsers();
      } catch (error) {
        console.error('Error adding user:', error);
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.response?.data?.detail || 'Failed to create user',
          life: 3000
        });
      } finally {
        this.addingUser = false;
      }
    },
    async loadUsers() {
      try {
        console.log('Loading users...');
        
        if (!this.isAdmin) {
          console.warn('User is not an admin, cannot load user list');
          this.users = [];
          return;
        }

        // Ensure we have a valid token
        const token = localStorage.getItem('access_token');
        if (!token) {
          throw new Error('No authentication token found');
        }

        const response = await axios.get('/auth/admin/users');
        console.log('Users response:', response.data);
        
        if (!Array.isArray(response.data)) {
          console.error('Expected array of users but got:', typeof response.data);
          this.toast.add({
            severity: 'error',
            summary: 'Error',
            detail: 'Invalid data format received from server',
            life: 3000
          });
          return;
        }
        
        this.users = response.data;
        console.log('Updated users array:', this.users);
      } catch (error) {
        console.error('Error loading users:', error);
        console.error('Error details:', error.response?.data);
        
        if (error.response?.status === 403) {
          console.warn('User does not have permission to view user list');
          this.toast.add({
            severity: 'warn',
            summary: 'Limited Access',
            detail: 'You do not have permission to view the user list.',
            life: 5000
          });
          this.users = [];
        } else {
          this.toast.add({
            severity: 'error',
            summary: 'Error',
            detail: error.response?.data?.detail || error.message || 'Failed to load users',
            life: 3000
          });
        }
      }
    },
    async updateUserRole(user) {
      try {
        await axios.put(`/auth/admin/users/${user.id}/role`, { role: user.role });
        this.toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'User role updated successfully',
          life: 3000
        });
      } catch (error) {
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to update user role',
          life: 3000
        });
      }
    },
    async showCollaboratorModal(user) {
      this.selectedUser = user;
      this.showModal = true;
      await this.loadCollaborators(user.id);
      await this.loadAvailableUsers(user.id);
    },
    async loadCollaborators(userId) {
      try {
        const response = await axios.get(`/auth/admin/users/${userId}/collaborators`);
        this.currentCollaborators = response.data;
      } catch (error) {
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load collaborators',
          life: 3000
        });
      }
    },
    async loadAvailableUsers(userId) {
      try {
        const response = await axios.get('/auth/admin/users');
        this.availableUsers = response.data.filter(user => user.id !== userId);
      } catch (error) {
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to load available users',
          life: 3000
        });
      }
    },
    async addCollaborator() {
      try {
        await axios.post(
          `/auth/admin/users/${this.selectedUser.id}/collaborator/${this.newCollaboratorId}`
        );
        await this.loadCollaborators(this.selectedUser.id);
        this.newCollaboratorId = null;
        this.toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Collaborator added successfully',
          life: 3000
        });
      } catch (error) {
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to add collaborator',
          life: 3000
        });
      }
    },
    async removeCollaborator(collaborator) {
      try {
        await axios.delete(
          `/auth/admin/users/${this.selectedUser.id}/collaborator/${collaborator.id}`
        );
        await this.loadCollaborators(this.selectedUser.id);
        this.toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Collaborator removed successfully',
          life: 3000
        });
      } catch (error) {
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to remove collaborator',
          life: 3000
        });
      }
    },
    closeModal() {
      this.showModal = false;
      this.selectedUser = null;
      this.currentCollaborators = [];
      this.availableUsers = [];
      this.newCollaboratorId = null;
    },
    async loadPersonalCollaborators() {
      try {
        const response = await axios.get('/auth/users/me/collaborators');
        this.personalCollaborators = response.data;
      } catch (error) {
        console.error('Error loading personal collaborators:', error);
        this.error = 'Failed to load collaborators';
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
        this.error = 'Failed to load available users';
      }
    },
    async addPersonalCollaborator() {
      if (!this.selectedPersonalUserId) return;
      
      try {
        await axios.post(`/auth/users/me/collaborators/${this.selectedPersonalUserId}`);
        await this.loadPersonalCollaborators();
        await this.loadAvailablePersonalUsers();
        this.selectedPersonalUserId = '';
      } catch (error) {
        console.error('Error adding personal collaborator:', error);
        this.error = 'Failed to add collaborator';
      }
    },
    async removePersonalCollaborator(collaboratorId) {
      try {
        await axios.delete(`/auth/users/me/collaborators/${collaboratorId}`);
        await this.loadPersonalCollaborators();
        await this.loadAvailablePersonalUsers();
      } catch (error) {
        console.error('Error removing personal collaborator:', error);
        this.error = 'Failed to remove collaborator';
      }
    },
    redirectToLogin() {
      this.$router.push('/login');
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
    },
    async bulkCreateUsers() {
      this.bulkCreating = true;
      this.bulkResults = [];
      
      try {
        const response = await axios.post('/auth/admin/users/bulk', { 
          data: this.bulkUserData 
        });
        
        this.bulkResults = response.data;
        
        // Count successes and failures
        const successCount = this.bulkResults.filter(r => r.success).length;
        const failureCount = this.bulkResults.filter(r => !r.success).length;
        
        if (successCount > 0) {
          this.toast.add({
            severity: 'success',
            summary: 'Bulk Creation Complete',
            detail: `${successCount} user(s) created successfully${failureCount > 0 ? `, ${failureCount} failed` : ''}`,
            life: 5000
          });
          
          // Refresh the user list if any users were created
          await this.loadUsers();
          
          // Clear the bulk data if all users were created successfully
          if (failureCount === 0) {
            this.bulkUserData = '';
          }
        } else {
          this.toast.add({
            severity: 'error',
            summary: 'Bulk Creation Failed',
            detail: `All ${failureCount} user creation(s) failed. Check the results below.`,
            life: 5000
          });
        }
        
      } catch (error) {
        console.error('Error bulk creating users:', error);
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.response?.data?.detail || 'Failed to create users',
          life: 3000
        });
      } finally {
        this.bulkCreating = false;
      }
    },
    async confirmDeleteUser(user) {
      this.userToDelete = user;
      this.showDeleteDialog = true;
    },
    async deleteUser() {
      this.deletingUser = true;
      try {
        await axios.delete(`/auth/admin/users/${this.userToDelete.id}`);
        this.toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'User deleted successfully',
          life: 3000
        });
        await this.loadUsers();
      } catch (error) {
        console.error('Error deleting user:', error);
        this.toast.add({
          severity: 'error',
          summary: 'Error',
          detail: error.response?.data?.detail || 'Failed to delete user',
          life: 3000
        });
      } finally {
        this.showDeleteDialog = false;
        this.deletingUser = false;
      }
    }
  },
  async created() {
    try {
      // First check auth status to ensure we have the latest user info
      await this.$store.dispatch('auth/checkAuthStatus');
      
      // Now check if user is admin
      if (!this.isAdmin) {
        console.warn('User is not an admin, showing warning message');
        this.toast.add({
          severity: 'warn',
          summary: 'Limited Access',
          detail: 'Some features may be restricted as you do not have admin privileges.',
          life: 5000
        });
      } else {
        // Only load users if admin
        await this.loadUsers();
      }
      
      // Load personal collaborators for both admin and private users
      if (this.userRole === 'admin' || this.userRole === 'private_user') {
        await Promise.all([
          this.loadPersonalCollaborators(),
          this.loadAvailablePersonalUsers()
        ]);
      }
    } catch (error) {
      console.error('Error in AdminDashboard created hook:', error);
      this.toast.add({
        severity: 'error',
        summary: 'Error',
        detail: 'Failed to initialize dashboard. Please try refreshing the page.',
        life: 5000
      });
    } finally {
      this.loadingPersonalCollaborators = false;
    }
  }
};
</script>

<style scoped>
.admin-dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
}

@media (max-width: 768px) {
  .admin-dashboard {
    padding: 1rem;
  }
  
  :deep(.p-dialog) {
    width: 90vw !important;
  }
}

/* Remove all other styles as they're now handled by PrimeVue classes */
</style> 