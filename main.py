from initializing_qiskit import initialize_qiskit
import logging

"""
Instance list:
rpi-rensselaer/general/general  (On-Campus Quantum Computer)
rpi/general/general             (Remote IBM Quantum Computer)
"""

# Main function to initialize the Qiskit Runtime Service
def main():
    # Initialize the Qiskit Runtime Service and Backend
    service, backend = initialize_qiskit(log_level=logging.INFO)

    # Put code for further processing here



if __name__ == "__main__":
    main()
