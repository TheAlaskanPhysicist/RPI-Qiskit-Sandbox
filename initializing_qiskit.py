from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit.providers import BackendV2
from argparse import ArgumentParser, Namespace
from dotenv import load_dotenv
import logging
import os


# Console parser function to handle command line arguments
def _console_parser() -> Namespace:
    """
    Creates and returns a Namespace for command line arguments.
    """
    # Parse command line arguments
    parser = ArgumentParser(description="Initialize IBM Qiskit Runtime Service")
    parser.add_argument("-i", "--instance", type=str, default=None, help="IBM Quantum Instance Name")
    parser.add_argument("-t", "--token"   , type=str, default=None, help="IBM Quantum API Token")
    parser.add_argument("-b", "--backend" , type=str, default=None, help="IBM Quantum Backend Name (optional)")
    args: Namespace = parser.parse_args()

    # Log the received command line arguments
    arg_strings = [
        f"args.instance={args.instance if args.instance else 'None'}",
        f"args.backend={args.backend if args.backend else 'None'}",
        f"args.token={args.token[:10] + '...' if args.token else None}"
    ]
    logging.debug("Commandline arguments received: " + ", ".join(arg_strings))

    # Return the parsed arguments as a Namespace
    return args

# Environment parser function to handle environment variables
def _environment_parser() -> Namespace:
    """
    Creates and returns a Namespace for environment variables.
    """
    # Load environment variables from .env file
    load_dotenv()
    env_instance = os.getenv("IBMQ_INSTANCE")
    env_backend = os.getenv("IBMQ_BACKEND")
    env_token = os.getenv("IBMQ_TOKEN")

    # Log the received environment variables
    arg_strings = [
        f"IBMQ_INSTANCE={env_instance if env_instance else 'None'}",
        f"IBMQ_BACKEND={env_backend if env_backend else 'None'}",
        f"IBMQ_TOKEN={env_token[:10] + '...' if env_token else None}"
    ]
    logging.debug("Environment variables received: " + ", ".join(arg_strings))

    # Return the environment variables as a Namespace
    return Namespace(instance=env_instance, backend=env_backend, token=env_token)


# Load the Qiskit Runtime Service with fallbacks from environment variables
def _load_qiskit_runtime_fallback(*, instance: str = None, token: str = None) -> QiskitRuntimeService:
    """
    Attempts to load QiskitRuntimeService with fallbacks in order of preference:
      1. CLI instance ad CLI token
      2. ENV instance and CLI token
      3. CLI instance and ENV token
      4. ENV instance and ENV token
    Fails only if all four attempts are invalid.
    """
    # Load environment variables from .env file
    env = _environment_parser()

    # Attempt to use the CLI token and instance directly
    if instance and token:
        label = "[1] CLI instance + CLI token"
        try:
            logging.info(f"Attempting to load Qiskit runtime service: {label}")
            service = QiskitRuntimeService(channel="ibm_quantum", instance=instance, token=token)
            logging.info(f"Successfully loaded Qiskit runtime service: {label}")
            print(f"Connected to Qiskit runtime service with instance: {instance}")
            return service
        except Exception as e:
            logging.error(f"Failed to load Qiskit runtime service: {label} - {e}")
            logging.warning(f"Attempting to load alternate Qiskit runtime service(s)")

    # Create a list of (allowed) alternate attempts in order of preference
    alt_attempts = []
    if instance and env.token:  # CLI instance and ENV token provided
        alt_attempts.append( ("[2] CLI instance + ENV token", instance, env.token) )
    if env.instance and token:  # ENV instance and CLI token provided
        alt_attempts.append( ("[3] ENV instance + CLI token", env.instance, token) )
    if env.instance and env.token:  # ENV instance and ENV token provided
        alt_attempts.append( ("[4] ENV instance + ENV token", env.instance, env.token) )

    # Iterate through the alternative attempts
    for (label, instance, token) in alt_attempts:
        try:
            logging.info(f"Attempting to load Qiskit runtime service: {label}")
            service = QiskitRuntimeService(channel="ibm_quantum", instance=instance, token=token)
            logging.info(f"Successfully loaded Qiskit runtime service: {label}")
            print(f"Connected to Qiskit runtime service with instance: {instance}")
            return service
        except Exception as e:
            logging.error(f"Failed to load Qiskit runtime service: {label} - {e}")

    # If all attempts fail, raise an error
    logging.error("All attempts to authenticate with IBM Quantum failed.")
    logging.error("Please check your environment variables or command line arguments.")
    logging.debug(f"CLI instance: {instance}, CLI token: {token[:10] + '...' if token else None}")
    logging.debug(f"ENV instance: {env.instance}, ENV token: {env.token[:10] + '...' if env.token else None}")
    raise RuntimeError("All attempts to authenticate with IBM Quantum failed.")

# Load the Qiskit Runtime Service without fallbacks
def _load_qiskit_runtime(instance: str = None, token: str = None) -> QiskitRuntimeService:
    """
    Loads the QiskitRuntimeService with the provided instance and token.
    This function does not handle fallbacks.
    """
    # Both instance and token must be provided
    if not (instance and token):
        logging.error("Both instance and token must be provided to load Qiskit runtime service.")
        raise ValueError("Both instance and token must be provided to load Qiskit runtime service.")

    # Attempt to load the Qiskit runtime service with the provided instance and token
    try:
        logging.info(f"Loading Qiskit runtime service with instance: {instance}, token: {token[:8]}...")
        service = QiskitRuntimeService(channel="ibm_quantum", instance=instance, token=token)
        logging.info("Successfully loaded Qiskit runtime service!")
        print(f"Connected to Qiskit runtime service with instance: {instance}")
        return service
    except Exception as e:
        logging.error(f"Failed to load Qiskit runtime service: {e}")
        raise RuntimeError(f"Failed to load Qiskit runtime service: {e}") from e

# Load the Qiskit Runtime Service
def load_qiskit_runtime(instance: str = None, token: str = None, fallback=False) -> QiskitRuntimeService:
    """
    Loads the QiskitRuntimeService with the provided instance and token.
    This function does not handle fallbacks.
    """
    if not fallback: return _load_qiskit_runtime(instance=instance, token=token)
    else: return _load_qiskit_runtime_fallback(instance=instance, token=token)


# Load the backend of the Qiskit Runtime Service with a fallback from environment variables
def _load_qiskit_backend_fallback(service: QiskitRuntimeService, backend_name: str = None) -> BackendV2:

    # Load environment variables from .env file
    env = _environment_parser()

    # Attempt to use the CLI backend name directly
    if backend_name:
        label = "[1] CLI backend name"
        try:
            logging.info(f"Attempting to load backend: {backend_name} from service: {service}")
            backend = service.backend(name=backend_name)
            logging.info(f"Connected to backend: {backend.name}")
            print(f"Connected to backend: {backend.name}")
            return backend
        except Exception as e:
            logging.error(f"Failed to connect to backend {backend_name}: {e}")
            logging.warning("Attempting to load alternate backends")

    # Use the environment variable backend name as a fallback
    if env.backend:
        label = "[2] ENV backend name"
        try:
            logging.info(f"Attempting to load backend: {env.backend} from service: {service}")
            backend = service.backend(name=env.backend)
            logging.info(f"Connected to backend: {backend.name}")
            print(f"Connected to backend: {backend.name}")
            return backend
        except Exception as e:
            logging.error(f"Failed to connect to backend {env.backend}: {e}")

    # If no backend name is provided, raise an error
    logging.error("No backend name provided and no environment variable for backend found.")
    raise ValueError("No backend name provided and no environment variable for backend found.")

# Load the backend of the Qiskit Runtime Service without a fallback
def _load_qiskit_backend(service: QiskitRuntimeService, backend_name: str = None) -> BackendV2:
    try:
        logging.info(f"Loading backend: {backend_name} from service: {service}")
        backend = service.backend(name=backend_name)
        logging.info(f"Connected to backend: {backend.name}")
        print(f"Connected to backend: {backend.name}")
        return backend
    except Exception as e:
        logging.error(f"Failed to connect to backend {backend_name}: {e}")
        raise RuntimeError(f"Failed to connect to backend {backend_name}: {e}") from e

# Load the backend of the Qiskit Runtime Service
def load_qiskit_backend(service: QiskitRuntimeService, backend_name: str = None, fallback=False) -> BackendV2:
    if not fallback: return _load_qiskit_backend(service=service, backend_name=backend_name)
    else: return _load_qiskit_backend_fallback(service=service, backend_name=backend_name)


# Initialize function to initialize the Qiskit Runtime Service
def initialize_qiskit(log_level: str|int|None=logging.WARNING, fallback: bool=False) -> tuple[QiskitRuntimeService, BackendV2]:

    # Set up logging
    logging.basicConfig(level=log_level, format='[%(levelname)s] %(asctime)s - %(message)s')

    # Load the Qiskit Runtime Service and Backend
    console: Namespace            = _console_parser()
    service: QiskitRuntimeService = load_qiskit_runtime(instance=console.instance, token=console.token, fallback=fallback)
    backend: BackendV2            = load_qiskit_backend(service=service, backend_name=None, fallback=fallback)

    # Print all backends available in the service
    logging.info(f"Available backends in service: " + ", ".join([backend.name for backend in service.backends()]))

    # Return the service and backend for further use
    return service, backend
