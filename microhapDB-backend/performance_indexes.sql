-- Performance optimization indexes for microhapDB
-- Run this script to add missing indexes that will improve query performance

-- Indexes for sequence_table
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sequence_species_version 
ON sequence_table (species, version_added);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sequence_alleleid_species 
ON sequence_table (alleleid, species);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sequence_version_added 
ON sequence_table (version_added);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sequence_info_gin 
ON sequence_table USING gin(to_tsvector('english', info));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sequence_trait_gin 
ON sequence_table USING gin(to_tsvector('english', associated_trait));

-- Indexes for database_versions
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_database_versions_species_version 
ON database_versions (species, version);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_database_versions_uploaded_by 
ON database_versions (uploaded_by);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_database_versions_program_species 
ON database_versions (program_id, species);

-- Indexes for allele_presence
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_allele_presence_species_version 
ON allele_presence (species, version_added);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_allele_presence_alleleid_species 
ON allele_presence (alleleid, species);

-- Indexes for sequence_presence
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sequence_presence_program_species 
ON sequence_presence (program_id, species);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sequence_presence_version 
ON sequence_presence (version_added);

-- Indexes for file_uploads (already partially indexed)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_file_uploads_species_version 
ON file_uploads (species, version);

-- Indexes for users table for role-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_role 
ON users (role);

-- Composite index for common query patterns
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sequence_species_alleleid_version 
ON sequence_table (species, alleleid, version_added);

-- Analyze tables after creating indexes
ANALYZE sequence_table;
ANALYZE database_versions;
ANALYZE allele_presence;
ANALYZE sequence_presence;
ANALYZE file_uploads;
ANALYZE users; 