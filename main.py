import qiskit
from qiskit_ibm_runtime import QiskitRuntimeService
from dotenv import load_dotenv
import os
from argparse import ArgumentParser





"""
Instance list:
rpi-rensselaer/general/general  (On-Campus Quantum Computer)
rpi/general/general             (Remote IBM Quantum Computer)
"""


def load_qiskit_runtime_service(*, cli_instance: str = None, cli_token: str = None) -> QiskitRuntimeService:
    """
    Attempts to load QiskitRuntimeService with fallbacks in order of preference:
      1. CLI token and CLI instance
      2. CLI token and ENV instance
      3. ENV token and CLI instance
      4. ENV token and ENV instance
    Fails only if all four attempts are invalid.
    """

    # Load environment variables from .env file
    load_dotenv()
    env_token = os.getenv("IBMQ_TOKEN")
    env_instance = os.getenv("IBMQ_INSTANCE")

    # Create a list of attempts in order of preference
    attempts = [
        ("[1] CLI token + CLI instance", cli_token, cli_instance),
        ("[2] CLI token + ENV instance", cli_token, env_instance),
        ("[3] ENV token + CLI instance", env_token, cli_instance),
        ("[4] ENV token + ENV instance", env_token, env_instance),
    ]

    # Iterate through attempts to find a valid service
    for label, token, instance in attempts:
        try:
            if not token or not instance: raise ValueError("Missing token or instance.")
            print(f"Trying {label}")
            return QiskitRuntimeService(channel="ibm_quantum", instance=instance, token=token)
        except Exception as e:
            print(f"{label} failed: {e}")

    # If all attempts fail, raise an error
    raise RuntimeError("All attempts to authenticate with IBM Quantum failed. Check your token and instance.")


def main():
    # Parse command line arguments
    parser: ArgumentParser = ArgumentParser(description="Initialize IBM Qiskit Runtime Service")
    parser.add_argument("-i", "--instance", type=str, default=None, help="IBM Quantum Instance Name")
    parser.add_argument("-t", "--token"   , type=str, default=None, help="IBM Quantum API Token")
    args = parser.parse_args()
    print(f"Arguments received: instance={args.instance}, token={args.token}")

    # Load the Qiskit Runtime Service with the provided arguments
    service: QiskitRuntimeService = load_qiskit_runtime_service(cli_token=args.token, cli_instance=args.instance)

    # Print the service information
    print(f"Successfully loaded IBM Quantum Runtime Service for instance: {service.instances()}")
    print("Available backends:")
    for backend in service.backends():
        print(f" - {backend.name}")





if __name__ == "__main__":
    main()

