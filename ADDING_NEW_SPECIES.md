# Adding New Species to MicrohapDB

This guide explains how to add new species to the MicrohapDB system. The process has been streamlined to make future additions easier.

## Overview

As of the latest update, the system supports the following species:
- Alfalfa (`alfalfa`)
- Sweetpotato (`sweetpotato`) 
- Cranberry (`cranberry`)
- Blueberry (`blueberry`)
- Pecan (`pecan`)
- Potato (`potato`)

## Quick Steps for Adding a New Species

### 1. Backend Configuration

#### Update Species Configuration
Edit `microhapDB-backend/src/config.py` and add your new species to the `SUPPORTED_SPECIES` list:

```python
SUPPORTED_SPECIES = [
    # ... existing species ...
    {
        "name": "YourNewSpecies",
        "value": "yournewspecies",  # lowercase, no spaces
        "display_name": "Your New Species"
    }
]
```

#### Create Database Migration
1. Navigate to the backend directory:
   ```bash
   cd microhapDB-backend
   ```

2. Create a new migration:
   ```bash
   alembic revision -m "add_yournewspecies_partition"
   ```

3. Edit the generated migration file in `alembic/versions/` to add the partition:
   ```python
   def upgrade() -> None:
       op.execute("""
           CREATE TABLE IF NOT EXISTS sequence_table_yournewspecies 
           PARTITION OF sequence_table FOR VALUES IN ('yournewspecies');
       """)

   def downgrade() -> None:
       op.execute("""
           DROP TABLE IF EXISTS sequence_table_yournewspecies;
       """)
   ```

4. Apply the migration:
   ```bash
   alembic upgrade head
   ```

### 2. Frontend Configuration

#### Update Species Configuration
Edit `microhapDB-frontend/src/utils/speciesConfig.js` and add your new species:

```javascript
export const SUPPORTED_SPECIES = [
  // ... existing species ...
  { label: 'Your New Species', value: 'yournewspecies' }
];

export const SPECIES_LIST = [
  // ... existing species ...
  { name: 'Your New Species', value: 'yournewspecies' }
];
```

That's it! The centralized configuration will automatically update all components.

## Manual Method (Legacy - Not Recommended)

If you need to update components manually, here are the files that previously required updates:

### Frontend Files
- `microhapDB-frontend/src/components/Visualizations2.vue`
- `microhapDB-frontend/src/components/Visualizations.vue`
- `microhapDB-frontend/src/components/Query.vue`
- `microhapDB-frontend/src/components/Report.vue`
- `microhapDB-frontend/src/components/FileUpload.vue`
- `microhapDB-frontend/src/components/SystemAdministration.vue`
- `microhapDB-frontend/src/components/DataUpload.vue`
- `microhapDB-frontend/src/assets/Alignment.vue` (if enabled)

### Backend Files
- `microhapDB-backend/src/models.py` (partition creation)
- `microhapDB-backend/src/brapi/brapi_endpoints.py` (if enabled)

## Database Considerations

### Partitioning
The system uses PostgreSQL table partitioning by species. Each species gets its own partition of the `sequence_table`. This improves query performance when filtering by species.

### Data Isolation
Each species maintains its own:
- Sequence data partition
- Database versions
- Program associations

## Testing New Species

After adding a new species:

1. **Frontend Testing:**
   - Verify the species appears in all dropdown menus
   - Test data upload functionality
   - Test visualization components
   - Test query functionality

2. **Backend Testing:**
   - Verify database partition was created
   - Test API endpoints with the new species
   - Test data upload and retrieval

3. **Database Testing:**
   - Check partition exists: `\d+ sequence_table` in psql
   - Verify data can be inserted and queried

## Troubleshooting

### Common Issues

1. **Migration Fails:**
   - Check database connection
   - Verify partition syntax
   - Ensure species value is lowercase and contains no spaces

2. **Frontend Not Showing New Species:**
   - Clear browser cache
   - Restart development server
   - Check for JavaScript errors in console

3. **API Errors:**
   - Verify backend configuration is correct
   - Check species validation in API endpoints
   - Restart backend server

### Rollback

To remove a species:

1. Create a new migration to drop the partition
2. Remove from configuration files
3. Clean up any existing data (if needed)

## Best Practices

1. **Naming Convention:**
   - Use lowercase values with no spaces
   - Use descriptive but concise names
   - Be consistent with existing naming patterns

2. **Testing:**
   - Always test in development environment first
   - Verify all components work with new species
   - Test data upload/download functionality

3. **Documentation:**
   - Update this file when adding species
   - Document any species-specific requirements
   - Update API documentation if needed

## Future Improvements

Consider implementing:
- Dynamic species loading from database
- Admin interface for species management
- Automated testing for new species
- Species-specific configuration options 