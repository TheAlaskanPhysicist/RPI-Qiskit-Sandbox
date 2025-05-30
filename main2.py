import qiskit
from qiskit.providers import BackendV2
from qiskit_ibm_runtime import QiskitRuntimeService
from dotenv import load_dotenv
import os
from argparse import ArgumentParser
import logging




"""
Instance list:
rpi-rensselaer/general/general  (On-Campus Quantum Computer)
rpi/general/general             (Remote IBM Quantum Computer)
"""


def load_qiskit_runtime(*, instance: str = None, token: str = None, backend: str = None) -> tuple[QiskitRuntimeService, BackendV2]:
    """
    Attempts to load QiskitRuntimeService with fallbacks in order of preference:
      1. CLI instance ad CLI token
      2. ENV instance and CLI token
      3. CLI instance and ENV token
      4. ENV instance and ENV token
    Fails only if all four attempts are invalid.
    """
    # Reassign CLI arguments to local variables for clarity
    cli_instance: str = instance
    cli_token: str = token
    cli_backend: str = backend

    # Load environment variables from .env file
    load_dotenv()
    env_token = os.getenv("IBMQ_TOKEN")
    env_instance = os.getenv("IBMQ_INSTANCE")
    env_backend = os.getenv("IBMQ_BACKEND")
    logging.debug(f"Environment variables received: IBQM_INSTANCE=\"{env_instance}\", IBQM_TOKEN={env_token[:10] + "..." if env_token else None}")

    # Attempt to use the CLI token and instance directly
    if cli_instance and cli_token:
        label = "[1] CLI instance + CLI token"
        try:
            logging.info(f"Attempting to load Qiskit runtime service: {label}")
            _service = QiskitRuntimeService(channel="ibm_quantum", instance=cli_instance, token=cli_token)
            _backend = _service.backend(name=cli_backend, instance=cli_instance)
            logging.info(f"Successfully loaded Qiskit runtime service: {label}")
            return _service, _backend
        except Exception as e:
            logging.error(f"Failed to load Qiskit runtime service: {label} - {e}")
            logging.warning(f"Attempting to load alternate Qiskit runtime service(s)")

    # Create a list of (allowed) alternate attempts in order of preference
    alt_attempts = []
    if cli_instance and env_token:  # CLI instance and ENV token provided
        alt_attempts.append( ("[2] CLI instance + ENV token", cli_instance, env_token, cli_backend) )
    if env_instance and cli_token:  # ENV instance and CLI token provided
        alt_attempts.append( ("[3] ENV instance + CLI token", env_instance, cli_token, env_backend) )
    if env_instance and env_token:  # ENV instance and ENV token provided
        alt_attempts.append( ("[4] ENV instance + ENV token", env_instance, env_token, env_backend) )

    # Iterate through the alternative attempts
    for (label, instance, token, backend) in alt_attempts:
        try:
            logging.info(f"Attempting to load Qiskit runtime service: {label}")
            _service = QiskitRuntimeService(channel="ibm_quantum", instance=instance, token=token)
            _backend = _service.backend(name=backend, instance=instance)
            logging.info(f"Successfully loaded Qiskit runtime service: {label}")
            return _service, _backend
        except Exception as e:
            logging.error(f"Failed to load Qiskit runtime service: {label} - {e}")
            print(f"{label} failed: {e}")

    # If all attempts fail, raise an error
    logging.error("All attempts to authenticate with IBM Quantum failed.")
    logging.error("Please check your environment variables or command line arguments.")
    logging.debug(f"CLI instance: {cli_instance}, CLI token: {cli_token[:10] + '...' if cli_token else None}")
    logging.debug(f"ENV instance: {env_instance}, ENV token: {env_token[:10] + '...' if env_token else None}")
    raise RuntimeError("All attempts to authenticate with IBM Quantum failed.")


def main2():
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s - %(message)s')

    # Parse command line arguments
    parser: ArgumentParser = ArgumentParser(description="Initialize IBM Qiskit Runtime Service")
    parser.add_argument("-i", "--instance", type=str, default=None, help="IBM Quantum Instance Name")
    parser.add_argument("-t", "--token"   , type=str, default=None, help="IBM Quantum API Token")
    parser.add_argument("-b", "--backend" , type=str, default=None, help="IBM Quantum Backend Name (optional)")
    args = parser.parse_args()
    logging.debug(f"Commandline arguments received: args.instance=\"{args.instance}\", args.token={args.token[:10] + "..." if args.token else None}")

    # Load the Qiskit Runtime Service with the provided arguments
    service, backend = load_qiskit_runtime(instance=args.instance, token=args.token, backend=args.backend)


    from qiskit import QuantumCircuit
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from qiskit_ibm_runtime import SamplerV2 as Sampler


    qc = QuantumCircuit(2)
    qc.h(0)
    # qc.h(1)
    qc.cx(0, 1)
    qc.measure_all()

    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_circuit = pm.run(qc)
    sampler = Sampler(backend)
    job = sampler.run([isa_circuit])
    print(f"job id: {job.job_id()}")

    result = job.result()
    print(result)

    # Get results from Databin
    pub_result = result[0]
    counts = pub_result.data.meas.get_counts()
    print(f"Counts for the meas output register: {counts}")

    # Plot results
    counts = {'00': 2006, '11': 2040, '10': 16, '01': 34}
    from qiskit.visualization import plot_histogram
    plot_histogram(counts)



def main():
    from qiskit import QuantumCircuit, QuantumRegister
    from matplotlib import pyplot as plt
    qubits = QuantumRegister(2, "q")
    circuit = QuantumCircuit(qubits)

    q0, q1 = qubits[0], qubits[1]
    circuit.h(q0)
    circuit.cx(q0, q1)
    circuit.measure_all()

    circuit.draw(output="mpl")
    plt.show()




if __name__ == "__main__":
    main()

