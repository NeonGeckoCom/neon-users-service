from neon_users_service.mq_connector import NeonUsersConnector
from ovos_utils import wait_for_exit_signal
from ovos_utils.log import LOG, init_service_logger

init_service_logger("neon-users-service")


def main():
    connector = NeonUsersConnector(None)
    LOG.info("Starting Neon Users Service")
    connector.run()
    LOG.info("Started Neon Users Service")
    wait_for_exit_signal()
    LOG.info("Shut down")


if __name__ == "__main__":
    main()
