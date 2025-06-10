# Species Synchronization Fix

## Problem Description

When adding alleleIDs to the Query List from the visualization2 modal, there was a species synchronization issue:

1. **No Species Selection**: When alleles were added from visualization2, the species wasn't automatically selected in the Query component
2. **Species Mismatch**: The Query component and visualization2 component maintained separate species selections
3. **Query List Reset**: Selecting a new species in the Query component would reset the entire query list, losing previously added alleles

## Root Cause

The issue was caused by two independent species management systems:

- **Visualization2 Component**: Used `selectedSpecies.value` (local reactive variable)
- **Query Component**: Used `store.state.query.species` (Vuex store)

These were not synchronized, causing the following workflow problems:

1. User selects "alfalfa" in visualization2
2. User adds alleles to query list (these alleles are from alfalfa)
3. User navigates to Query component
4. Query component shows no species selected (or previously selected species)
5. User selects "alfalfa" in Query component
6. Query component resets the query list (thinking it's a species change)

## Solution Implemented

### 1. Species Synchronization in Visualization2

Modified `fetchSequenceAndAddToQueryList()` function in `Visualizations2.vue`:

```javascript
// Update the query state species to match the current visualization species
// This ensures the Query component shows the correct species
store.commit('setQueryState', { species: selectedSpecies.value });
```

**Location**: `microhapDB-frontend/src/components/Visualizations2.vue` (lines ~1796-1798)

This ensures that when alleles are added from visualization2, the Query component's species selection is automatically synchronized.

### 2. User Confirmation in Query Component

Modified the species watcher in `Query.vue` to properly handle confirmation before allowing species changes:

```javascript
data() {
  return {
    // ... other data properties
    isReverting: false // Flag to prevent infinite loops during revert
  };
},
watch: {
  species(newVal, oldVal) {
    if (newVal !== oldVal) {
      // Skip confirmation if we're in the middle of a revert operation
      if (this.isReverting) {
        this.isReverting = false;
        return;
      }
      
      // Check if there are selected sequences and we need confirmation
      if (this.selectedSequences.length > 0 && oldVal !== '') {
        // Use PrimeVue's confirmation dialog for better UX
        this.$confirm.require({
          message: `You have ${this.selectedSequences.length} allele(s) in your query list. Changing species will clear your current query list. Do you want to continue?`,
          header: 'Species Change Confirmation',
          icon: 'pi pi-exclamation-triangle',
          rejectClass: 'p-button-secondary p-button-outlined',
          rejectLabel: 'Cancel',
          acceptLabel: 'Continue',
          accept: () => {
            // User confirmed - proceed with species change
            this.resetSelection();
            this.updateQueryState({ page: 1 });
            this.fetchSequences();
          },
          reject: () => {
            // User cancelled - revert the species change
            this.isReverting = true;
            this.updateQueryState({ species: oldVal });
          }
        });
        return; // Don't proceed with automatic change
      }
      
      // Proceed with species change (only if no confirmation needed)
      this.resetSelection();
      this.updateQueryState({ page: 1 });
      this.fetchSequences();
    }
  }
}
```

**Location**: `microhapDB-frontend/src/components/Query.vue` (species watcher)

**Key Fix**: Moved confirmation logic from `@change` event handler to the species watcher to properly intercept and revert species changes when user cancels. The watcher receives both the new and old values, allowing proper reversion.

**UI Enhancement**: Uses PrimeVue's ConfirmDialog component for consistent styling and better user experience, replacing the basic native `confirm()` dialog.

## Bug Fix: Species Change Confirmation

**Issue**: The initial implementation had a timing problem where the dropdown's `v-model` binding would update the species immediately, before the confirmation dialog could prevent the change.

**Additional Issue**: The first fix attempt created an infinite loop - when user clicked "Cancel", the revert operation would trigger the watcher again, causing the confirmation dialog to appear repeatedly.

**Solution**: 
- Removed `@change` event handler from dropdown
- Moved confirmation logic to the `species` watcher
- Used `oldVal` parameter to properly revert species when user cancels
- **Added `isReverting` flag** to distinguish between user-initiated changes and programmatic reverts
- When reverting, set `isReverting = true` before updating species to prevent watcher from triggering confirmation again
- **Implemented PrimeVue ConfirmDialog** for consistent UI styling and better user experience

## Benefits

1. **Automatic Synchronization**: Species is automatically set in Query component when alleles are added from visualization2
2. **User Control**: Users are warned before their query list is cleared
3. **Improved UX**: Clear feedback about what actions will affect the query list
4. **Data Preservation**: Users can cancel species changes to preserve their query list
5. **Filter Clearing**: Search filters are automatically cleared when changing species to prevent confusion from stale filter values
6. **Filter Preservation**: Using search filters no longer clears the query list - users can filter the table while maintaining their selected alleles

## Testing Instructions

### Test Case 1: Species Synchronization
1. Navigate to visualization2 
2. Select a species (e.g., "alfalfa")
3. Load data and add alleles to query list
4. Navigate to Query component
5. **Expected**: Species should already be set to "alfalfa"

### Test Case 2: Species Change Warning
1. Have alleles in query list
2. Try to change species in Query component
3. **Expected**: Confirmation dialog should appear
4. Click "Cancel" - species should revert, query list preserved
5. Click "OK" - species should change, query list cleared

### Test Case 3: Empty Query List
1. Ensure query list is empty
2. Change species in Query component
3. **Expected**: No confirmation dialog, species changes immediately

### Test Case 4: Filter Clearing
1. Select a species and enter some filter values (e.g., search for specific Allele ID)
2. Change to a different species
3. **Expected**: All filter fields should be cleared and show placeholder text

### Test Case 5: Filter Preservation
1. Select some alleles and add them to your query list
2. Type in any filter field (e.g., search for specific Allele ID)
3. **Expected**: Query list count should remain unchanged, selected alleles preserved

## Files Modified

1. `microhapDB-frontend/src/components/Visualizations2.vue`
   - Modified `fetchSequenceAndAddToQueryList()` function
   - Added species synchronization logic

2. `microhapDB-frontend/src/components/Query.vue`
   - Modified `handleSpeciesChange()` function
   - Added user confirmation for species changes

## Technical Notes

- Uses PrimeVue's ConfirmDialog service for consistent UI styling and behavior
- Leverages existing Vuex store structure
- Maintains backward compatibility
- No breaking changes to existing API or data structures
- Includes proper infinite loop prevention with `isReverting` flag

## Future Enhancements

Consider implementing:
1. More sophisticated species validation (checking if alleles actually belong to selected species)
2. Visual indicators showing which species each allele belongs to
3. Ability to filter query list by species rather than clearing it
4. Toast notifications for better user feedback 