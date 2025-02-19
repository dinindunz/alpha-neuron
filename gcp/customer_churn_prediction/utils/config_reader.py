import yaml

def read_config(config_path="config/config.yaml"):
    """Reads the configuration from a YAML file."""
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    return config
