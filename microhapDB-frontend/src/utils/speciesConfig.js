// Centralized species configuration for the frontend
// This makes it easier to add new species in the future

export const SUPPORTED_SPECIES = [
  { label: 'Alfalfa', value: 'alfalfa' },
  { label: 'Sweetpotato', value: 'sweetpotato' },
  { label: 'Cranberry', value: 'cranberry' },
  { label: 'Blueberry', value: 'blueberry' },
  { label: 'Pecan', value: 'pecan' },
  { label: 'Potato', value: 'potato' }
];

// Alternative format for components that need different structure
export const SPECIES_LIST = [
  { name: 'Alfalfa', value: 'alfalfa' },
  { name: 'Sweet Potato', value: 'sweetpotato' },
  { name: 'Cranberry', value: 'cranberry' },
  { name: 'Blueberry', value: 'blueberry' },
  { name: 'Pecan', value: 'pecan' },
  { name: 'Potato', value: 'potato' }
];

// Helper functions
export const getSpeciesValues = () => {
  return SUPPORTED_SPECIES.map(species => species.value);
};

export const getSpeciesLabels = () => {
  return SUPPORTED_SPECIES.map(species => species.label);
};

export const isValidSpecies = (speciesValue) => {
  return getSpeciesValues().includes(speciesValue);
};

export const getSpeciesLabel = (speciesValue) => {
  const species = SUPPORTED_SPECIES.find(s => s.value === speciesValue);
  return species ? species.label : speciesValue;
};

export default SUPPORTED_SPECIES; 