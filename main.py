from enum import Enum

from initializing_qiskit import initialize_qiskit
from qiskit_ibm_runtime import QiskitRuntimeService
from qiskit_aer import Aer, AerSimulator
from qiskit_aer.noise import NoiseModel
from dotenv import load_dotenv
import logging
import os
from argparse import Namespace, ArgumentParser
"""
Instance list:
rpi-rensselaer/general/general  (On-Campus Quantum Computer)
rpi/general/general             (Remote IBM Quantum Computer)
"""




# Environment parser function to handle environment variables
def environment_parser() -> Namespace:
    """
    Creates and returns a Namespace for environment variables.
    """
    # Load environment variables from .env file
    load_dotenv()
    env_instance = os.getenv("IBMQ_INSTANCE")
    env_backend = os.getenv("IBMQ_BACKEND")
    env_token = os.getenv("IBMQ_TOKEN")
    env_shots = os.getenv("IBMQ_SHOTS", "1024")

    # Log the received environment variables
    arg_strings = [
        f"IBMQ_INSTANCE={env_instance if env_instance else 'None'}",
        f"IBMQ_BACKEND={env_backend if env_backend else 'None'}",
        f"IBMQ_SHOTS={env_shots}",
        f"IBMQ_TOKEN={env_token[:10] + '...' if env_token else None}",
    ]
    logging.debug("Environment variables received:\n\tEnvironmentArgs(" + ", ".join(arg_strings) + ")")

    # Return the environment variables as a Namespace
    return Namespace(instance=env_instance, backend=env_backend, token=env_token, shots=int(env_shots))




"""
--env : Override command line arguments with environment variables
--config : Use a configuration file to set the parameters (does not include key)
--offline : Run on local simulator instead of IBMQ

--instance : Quantum instance (e.g., 'rpi-rensselaer/general/general')
--backend : Quantum backend name (e.g., 'ibm_rensselaer')
--shots : Number of shots to run the circuit (default: 1024)
--key : Quantum API key file path (default: None, uses environment variable 'IBMQ_TOKEN')
"""






# Console parser function to handle command line arguments
def console_parser() -> Namespace:
    """
    Creates and returns a Namespace for command line arguments.
    """
    # Parse command line arguments
    parser = ArgumentParser(description="Qiskit Runtime Service and Backend Initialization Handler")
    parser.add_argument(      "--offline",  action="store_true",     help="Run on local simulator instead of IBMQ")
    parser.add_argument(      "--env",      action="store_true",     help="Override command line arguments with environment variables")
    parser.add_argument("-i", "--instance", type=str,  default=None, help="Quantum instance (e.g., 'rpi-rensselaer/general/general')")
    parser.add_argument("-b", "--backend",  type=str,  default=None, help="Quantum backend name (e.g., 'ibm_rensselaer')")
    parser.add_argument("-n", "--shots",    type=int,  default=1024, help="Number of shots to run the circuit (default: 1024)")
    parser.add_argument("-k", "--key",      type=str,  default=None, help="Quantum API key file path (default: None, uses environment variable 'IBMQ_TOKEN')")
    args: Namespace = parser.parse_args()

    # Override command line arguments with environment variables if --env is specified
    if args.env:
        if any([args.instance, args.backend, args.shots, args.key]):
            logging.warning("Command line arguments will be overridden by environment variables.")
        env = environment_parser()
        args.instance = args.instance if not env.instance else env.instance
        args.backend = args.backend if not env.backend else env.backend
        args.shots = args.shots if not env.shots else env.shots
        args.key = args.key if not env.token else env.token

    # Load the token from the specified key file or environment variable
    elif args.key:
        try:
            with open(args.key, 'r') as file: args.key = file.read().strip()
        except FileNotFoundError:
            raise FileNotFoundError(f"Key file '{args.key}' not found.")
        except Exception as e:
            raise RuntimeError(f"Failed to read key file '{args.key}': {e}")

    # If no key is provided, use the environment variable
    elif not args.offline:
        args.key = environment_parser().token

    # Log the received command line arguments
    arg_strings = [
        f"args.offline={args.offline}",
        f"args.instance={args.instance if args.instance else 'None'}",
        f"args.backend={args.backend if args.backend  else 'None'}",
        f"args.shots={args.shots}",
        f"args.key={args.key[:10] + '...' if args.key else None}"
    ]
    logging.debug("Commandline arguments received:\n\tConsoleArgs(" + ", ".join(arg_strings) + ")")

    # Return the parsed arguments as a Namespace
    return args




# Backend creation
# If offline:
#      if all args are provided, load noise model from real backend
#      if partial args are provided, use AerSimulator without noise model and print warning
#      if no args are provided, use AerSimulator without noise model
# If online:
#      if all args are provided, connect to IBM backend
#      if not all args are provided, raise ValueError



def get_qiskit_runtime_service(args) -> tuple[QiskitRuntimeService|None, AerSimulator, NoiseModel|None]:
    """
    Initializes the Qiskit Runtime Service based on the provided command line arguments.
    """
    # Check if token is provided. If not, fall back to environment variables.
    if not args.token: args.token = _environment_parser().token

    # If offline mode is enabled, load noise model from real backend if all args are provided
    if args.offline:
        if args.token and args.instance and args.backend:
            try:
                service = QiskitRuntimeService(channel="ibm_quantum", token=args.token, instance=args.instance)
                real_backend = service.backend(args.backend)
                noise_model = NoiseModel.from_backend(real_backend)
                backend = AerSimulator(noise_model=noise_model)
                print(f"Loaded noise model from real backend: {args.backend}")
                return service, backend, noise_model
            except Exception as e:
                print(f"[WARNING] Failed to load noise model from backend '{args.backend}': {e}")
                backend = AerSimulator()
        elif any([args.token, args.instance, args.backend]):
            print("[WARNING] Partial credentials provided. Noise model will not be generated.")
            return None, AerSimulator(), None
        else:
            print("Running in offline mode. No connection to IBM Quantum required.")
            return None, AerSimulator(), None

    # Online execution: Requires token, instance, and backend
    else:
        if not (args.token and args.instance and args.backend):
            raise ValueError("Online execution requires --token, --instance, and --backend.")
        service = QiskitRuntimeService(channel="ibm_quantum", token=args.token, instance=args.instance)
        backend = service.backend(args.backend)
        print(f"Connected to IBM backend: {args.backend}")






    if not (args.token and args.instance):
        raise ValueError("Both --token and --instance must be provided to initialize Qiskit Runtime Service.")

    try:
        service = QiskitRuntimeService(channel="ibm_quantum", token=args.token, instance=args.instance)
        print(f"Connected to Qiskit Runtime Service: {args.instance}")
        return service
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Qiskit Runtime Service: {e}")





# Main function to initialize the Qiskit Runtime Service
def main():
    # Set up logging
    logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(asctime)s - %(message)s')

    args = console_parser()



    # # Initialize the Qiskit Runtime Service and Backend
    # args = console_parser()
    # service, backend = get_backend(args)
    #
    #
    # # Put code for further processing here
    # from qiskit import QuantumCircuit, transpile
    #
    # qc = QuantumCircuit(2, 2)
    # qc.h(0)
    # qc.cx(0, 1)
    # qc.measure([0, 1], [0, 1])
    #
    # transpiled = transpile(qc, backend)
    # job = backend.run(transpiled, shots=args.shots)
    # result = job.result()
    #
    # print(result.get_counts())


# Available:
# rpi/general/general
#  -> ibm_brisbane
#  -> ibm_sherbrooke

if __name__ == "__main__":
    main()
