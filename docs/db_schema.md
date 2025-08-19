# Schéma de base de données PostgreSQL

## Table: `labs`
- `id` (UUID, Primary Key)
- `name` (VARCHAR, Unique)
- `description` (TEXT)
- `status` (VARCHAR, e.g., 'created', 'deploying', 'deployed', 'error', 'deleted')
- `created_at` (TIMESTAMP, Default: NOW())
- `updated_at` (TIMESTAMP, Default: NOW())

## Table: `vms`
- `id` (UUID, Primary Key)
- `lab_id` (UUID, Foreign Key to `labs.id`)
- `name` (VARCHAR, Unique within lab)
- `vcpu` (INTEGER)
- `ram_mb` (INTEGER)
- `disk_gb` (INTEGER)
- `os_image` (VARCHAR, e.g., 'ubuntu-22.04', 'centos-stream-9')
- `ssh_port` (INTEGER, Unique)
- `vnc_port` (INTEGER, Unique)
- `status` (VARCHAR, e.g., 'pending', 'running', 'stopped', 'error')
- `ansible_config_yaml` (TEXT, Optional)
- `terraform_state` (TEXT, Optional)
- `created_at` (TIMESTAMP, Default: NOW())
- `updated_at` (TIMESTAMP, Default: NOW())

## Table: `tags`
- `id` (UUID, Primary Key)
- `name` (VARCHAR, Unique)

## Table: `lab_tags` (Junction Table)
- `lab_id` (UUID, Foreign Key to `labs.id`)
- `tag_id` (UUID, Foreign Key to `tags.id`)
- Primary Key (`lab_id`, `tag_id`)


