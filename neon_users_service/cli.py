# Copyright (C) 2008-2026 Neongecko.com Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Optional
from os import environ

import click

from neon_users_service.exceptions import UserExistsError


@click.group("neon-users-service",
             help="Neon Users Service commandline interface.")
def neon_users_service_cli():
    pass


@neon_users_service_cli.command(help="Start the Neon Users Service")
@click.option("--health-check-server-port", "-hp", type=int, default=None,
              help="Port for the health check server to listen on. Defaults "
                   "to the `HEALTHCHECK_PORT` environment variable.")
def run(health_check_server_port: Optional[int] = None):
    """
    Start the Neon Users Service MQ connector and run until terminated.
    """
    from ovos_utils import wait_for_exit_signal
    from ovos_utils.log import init_service_logger
    from neon_utils.process_utils import start_health_check_server
    from neon_users_service.mq_connector import NeonUsersConnector

    init_service_logger("neon-users-service")
    connector = NeonUsersConnector(None)
    click.echo("Starting Neon Users Service")
    status_port = health_check_server_port or environ.get("HEALTHCHECK_PORT")
    if status_port:
        start_health_check_server(connector.status, int(status_port),
                                  connector.check_health)
    connector.run()
    click.echo("Started Neon Users Service")
    wait_for_exit_signal()
    click.echo("Neon Users Service Shutdown")


@neon_users_service_cli.command(help="Create an admin-privileged user.")
@click.option("--username", "-u", default=None,
              help="Username of the admin user to create")
@click.option("--password", "-p", default=None,
              help="Password for the new admin user. If not provided, you "
                   "will be prompted to enter one securely.")
def create_admin(username: str, password: str):
    """
    Create a new admin user with the given USERNAME.
    """
    from neon_users_service.util.manage_user_db import create_admin_user
    if not username:
        username = click.prompt("Username", hide_input=False,
                                confirmation_prompt=False)
    if not password:
        password = click.prompt("Password", hide_input=True,
                                confirmation_prompt=True)
    try:
        user = create_admin_user(username, password)
        click.echo(f"Created admin user '{user.username}' ({user.user_id})")
    except UserExistsError:
        click.echo(f"FAILED TO CREATE. Username already exists: `{username}`")


if __name__ == "__main__":
    neon_users_service_cli()
