# Neon Users Service
This module manages access to a pluggable user database backend. By default, it
operates as a standalone module using SQLite as the persistent data store.

## Configuration
Configuration may be passed directly to the `NeonUsersService` constructor,
otherwise it will read from a config file using `ovos-config`. The configuration
file will be `~/.config/neon/diana.yaml` by default. An example valid configuration
is included:

```yaml
neon_users_service:
  module: sqlite
  sqlite:
    db_path: ~/.local/share/neon/user-db.sqlite
```

`module` defines the backend to use and a config key matching that backend
will specify the kwargs passed to the initialization of that module.