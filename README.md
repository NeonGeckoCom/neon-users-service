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

## MQ Integration
The `mq_connector` module provides an MQ entrypoint to services and is the
primary method of interaction with this service. Valid requests are detailed
below. Responses will always follow the form:

```yaml
success: False
error: <string description>
```

```yaml
success: True
user: <serialized User object>
```

### Create
Create a new user by sending a request with the following parameters:
```yaml
operation: create
username: <new_username>
password: <new_password>
user: <Optional serialized User object, else default will be created>
```

### Read
Read an existing user. If `password` is not supplied, then the returned User
object will have the `password_hash` and `tokens` config redacted.
```yaml
operation: read
username: <existing_username>
password: <existing_password>
```

### Update
Update an existing user. If a `password` is supplied, it will replace the
user's current password. If no `password` is supplied and `user.password_hash` 
is updated, the database entry will be updated with that new value.

```yaml
operation: update
username: <existing_username>
password: <optional new password>
user: <updated User object>
```

### Delete
Delete an existing user. This requires that the supplied `user` object matches
an entry in the database exactly for validation.
```yaml
operation: delete
username: <username_to_delete>
user: <User object to delete>
```

___
### Licensing
This project is free to use under the 
[GNU Affero General Public License](https://www.gnu.org/licenses/why-affero-gpl.html).
Contact info@neon.ai for commercial licensing options.
