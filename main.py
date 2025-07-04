from config.config_manager import ConfigManager
from config.logging_config import get_logger
from workflow.order.verification import OrderVerification
from utils.log_viewer import LogViewer
from ui.app import RegistrarApp
import argparse

logger = get_logger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Registrar Operations Center System")
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    args = parser.parse_args()

    config = ConfigManager(test=args.test)
    order_verification = OrderVerification(config)
    log_viewer = LogViewer(quiet=True)

    app = RegistrarApp(config, order_verification, log_viewer)
    app.run()

if __name__ == "__main__":
    main() 