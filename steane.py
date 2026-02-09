import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit import transpile
from qiskit.quantum_info import Statevector


def steane_encode():
    qc = QuantumCircuit(7)

    qc.h(1)
    qc.h(2)
    qc.h(3)

    qc.cx(1, 0)
    qc.cx(2, 0)
    qc.cx(3, 0)

    qc.cx(1, 4)
    qc.cx(2, 5)
    qc.cx(3, 6)

    return qc

def inject_error(qc, qubit, error_type):
    """
    error_type: 'X', 'Z' o 'Y'
    """
    if error_type == 'X':
        qc.x(qubit)
    elif error_type == 'Z':
        qc.z(qubit)
    elif error_type == 'Y':
        qc.y(qubit)
    else:
        raise ValueError("Tipo de error inválido")


def measure_bit_flip_syndrome(qc):
    """
    Devuelve un circuito con medición de síndrome X
    Usa 3 ancillas → 3 bits clásicos
    """
    qc_s = QuantumCircuit(10, 3)

    # Copiamos el circuito original
    qc_s.compose(qc, range(7), inplace=True)

    # Ancillas: qubits 7,8,9
    # Estabilizadores de Steane (Z-type)
    stabilizers = [
        [0, 2, 4, 6],
        [1, 2, 5, 6],
        [3, 4, 5, 6]
    ]

    for i, stab in enumerate(stabilizers):
        for q in stab:
            qc_s.cx(q, 7 + i)
        qc_s.measure(7 + i, i)

    return qc_s

SYNDROME_TABLE_X = {
    '001': 0,
    '010': 1,
    '011': 2,
    '100': 3,
    '101': 4,
    '110': 5,
    '111': 6
}

def correct_bit_flip(qc, syndrome):
    if syndrome in SYNDROME_TABLE_X:
        qubit = SYNDROME_TABLE_X[syndrome]
        qc.x(qubit)



def run_experiment(error_qubit, error_type, shots=1024):
    qc = steane_encode()
    inject_error(qc, error_qubit, error_type)

    qc_syndrome = measure_bit_flip_syndrome(qc)

    backend = Aer.get_backend('qasm_simulator')
    compiled = transpile(qc_syndrome, backend)
    job = backend.run(compiled, shots=shots)

    result = job.result()
    counts = result.get_counts()

    print(f"\nError {error_type} en qubit {error_qubit}")
    print("Resultados del síndrome:")
    for k, v in counts.items():
        print(f"Síndrome {k[::-1]} → {v} veces")

    return counts


if __name__ == "__main__":
    # Error X en el qubit 3
    run_experiment(error_qubit=3, error_type='X')

    # Error X en el qubit 6
    run_experiment(error_qubit=6, error_type='X')


