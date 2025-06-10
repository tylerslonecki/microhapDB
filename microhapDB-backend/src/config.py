# Global configurations

# Supported species configuration
SUPPORTED_SPECIES = [
    {
        "name": "Alfalfa",
        "value": "alfalfa",
        "display_name": "Alfalfa"
    },
    {
        "name": "Sweetpotato", 
        "value": "sweetpotato",
        "display_name": "Sweet Potato"
    },
    {
        "name": "Cranberry",
        "value": "cranberry", 
        "display_name": "Cranberry"
    },
    {
        "name": "Blueberry",
        "value": "blueberry",
        "display_name": "Blueberry"
    },
    {
        "name": "Pecan",
        "value": "pecan",
        "display_name": "Pecan"
    },
    {
        "name": "Potato",
        "value": "potato",
        "display_name": "Potato"
    }
]

# Helper functions for species management
def get_species_values():
    """Get list of species values for validation"""
    return [species["value"] for species in SUPPORTED_SPECIES]

def get_species_display_names():
    """Get list of species display names"""
    return [species["display_name"] for species in SUPPORTED_SPECIES]

def is_valid_species(species_value):
    """Check if a species value is valid"""
    return species_value in get_species_values()

def get_species_partition_commands():
    """Generate partition creation commands for all species"""
    commands = []
    for species in SUPPORTED_SPECIES:
        commands.append(
            f"CREATE TABLE IF NOT EXISTS sequence_table_{species['value']} "
            f"PARTITION OF sequence_table FOR VALUES IN ('{species['value']}');"
        )
    return commands