#!/usr/bin/env python3

import sys
import yaml
from typing import Dict, Any, List
from dataclasses import dataclass
import argparse

@dataclass
# Configuration for a Docker service
class ServiceConfig:
    name: str
    image: str
    entrypoint: str
    environment: List[str]
    networks: List[str]
    depends_on: List[str] = None
    container_name: str = None
    
    def __post_init__(self):
        if self.container_name is None:
            self.container_name = self.name

# Generator for Docker Compose files
class DockerComposeGenerator:
    def __init__(self, project_name: str = "tp0"):
        self.project_name = project_name
        self.services: Dict[str, Dict[str, Any]] = {}
        self.networks: Dict[str, Dict[str, Any]] = {}
    
    # Add a network to the compose file
    def add_network(self, name: str, subnet: str = None) -> None:
        network_config = {}
        if subnet:
            network_config = {
                'ipam': {
                    'driver': 'default',
                    'config': [{'subnet': subnet}]
                }
            }
        
        self.networks[name] = network_config

    # Add a service to the compose file
    def add_service(self, config: ServiceConfig) -> None:
        service_config = {
            'container_name': config.container_name,
            'image': config.image,
            'entrypoint': config.entrypoint,
            'environment': config.environment,
            'networks': config.networks
        }
        
        if config.depends_on:
            service_config['depends_on'] = config.depends_on
        
        self.services[config.name] = service_config

    # Generate server service configuration
    def generate_server_service(self) -> ServiceConfig:
        return ServiceConfig(
            name='server',
            image='server:latest',
            entrypoint='python3 /main.py',
            environment=[
                'PYTHONUNBUFFERED=1',
                'LOGGING_LEVEL=DEBUG'
            ],
            networks=['testing_net']
        )

    # Generate client service configuration
    def generate_client_service(self, client_id: int) -> ServiceConfig:
        return ServiceConfig(
            name=f'client{client_id}',
            image='client:latest',
            entrypoint='/client',
            environment=[
                f'CLI_ID={client_id}',
                'CLI_LOG_LEVEL=DEBUG'
            ],
            networks=['testing_net'],
            depends_on=['server']
        )

    # Convert generator to dictionary structure for YAML
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.project_name,
            'services': self.services,
            'networks': self.networks
        }

    # Write the compose configuration to a file
    def write_to_file(self, output_file: str) -> None:
        try:
            with open(output_file, 'w') as f:
                yaml.dump(
                    self.to_dict(), 
                    f, 
                    default_flow_style=False, 
                    sort_keys=False, 
                    indent=2
                )
            print(f"Successfully generated {output_file}")
        except Exception as e:
            print(f"Error writing file {output_file}: {e}")
            sys.exit(1)

# Create the Docker Compose file
def create_docker_compose(output_file: str, num_clients: int) -> None:
    generator = DockerComposeGenerator()
    
    generator.add_network('testing_net', '172.25.125.0/24')

    server_config = generator.generate_server_service()
    generator.add_service(server_config)
    
    for i in range(1, num_clients + 1):
        client_config = generator.generate_client_service(i)
        generator.add_service(client_config)
    
    generator.write_to_file(output_file)
    print(f"Generated {output_file} with {num_clients} clients")

def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Generate Docker Compose file with multiple clients'
    )
    parser.add_argument(
        'output_file',
        help='Output Docker Compose file name'
    )
    parser.add_argument(
        'num_clients',
        type=int,
        help='Number of client containers to create'
    )
    parser.add_argument(
        '--project-name',
        default='tp0',
        help='Docker Compose project name'
    )
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    try:
        create_docker_compose(args.output_file, args.num_clients)
    except Exception as e:
        print(f"Error generating Docker Compose: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()