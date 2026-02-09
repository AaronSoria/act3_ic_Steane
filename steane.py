import numpy as np
from qiskit import QuantumCircuit
from qiskit_aer import Aer
from qiskit import transpile
from qiskit.quantum_info import Statevector
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler

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


def get_backend(
    qubits_required=7,
    channel="ibm_quantum_platform",
    simulation=False
):
    if simulation:
        return Aer.get_backend("qasm_simulator")

    service = QiskitRuntimeService(channel=channel)

    candidates = service.backends(
        simulator=False,
        operational=True,
        min_num_qubits=qubits_required
    )

    if not candidates:
        raise RuntimeError(
            f"No hay backends con al menos {qubits_required} qubits disponibles."
        )

    candidates.sort(
        key=lambda b: b.status().pending_jobs
    )

    selected = candidates[0]

    print(
        f"Backend seleccionado automáticamente: "
        f"{selected.name} | "
        f"qubits={selected.num_qubits} | "
        f"cola={selected.status().pending_jobs}"
    )

    return selected

def execute_circuit(circuit, backend, shots=1024):
    """
    Ejecuta un circuito tanto en simulador como en hardware real IBM
    compatible con Sampler V2
    """

    # ---------- SIMULADOR (Aer) ----------
    if backend.__class__.__module__.startswith("qiskit_aer"):
        compiled = transpile(circuit, backend)
        job = backend.run(compiled, shots=shots)
        return job.result()

    # ---------- HARDWARE REAL (IBM Quantum, Sampler V2) ----------
    #service = QiskitRuntimeService(channel="ibm_quantum_platform")

    compiled = transpile(
        circuit,
        backend,
        optimization_level=1
    )

    sampler = Sampler(mode=backend)
    job = sampler.run([compiled], shots=shots)
    return job.result()


def run_experiment(qc, backend, shots=1024):
    result = execute_circuit(qc, backend, shots)

    # ---------- SIMULADOR ----------
    if hasattr(result, "get_counts"):
        counts = result.get_counts()

    # ---------- HARDWARE REAL (Sampler V2, IBM way) ----------
    else:
        # Tomamos el primer pub (solo enviamos un circuito)
        pub_result = result[0]

        # Nombre del registro clásico (por ej. 'c')
        creg_name = qc.cregs[0].name

        counts = getattr(pub_result.data, creg_name).get_counts()

    print("Resultados del síndrome:")
    for k, v in counts.items():
        print(f"Síndrome {k[::-1]} → {v} veces")

    return counts


def run_steane_experiment(
    error_qubit,
    error_type,
    shots=1024,
    backend=None
):
    qc = steane_encode()
    inject_error(qc, error_qubit, error_type)
    qc_syndrome = measure_bit_flip_syndrome(qc)

    print(f"\nError {error_type} en qubit {error_qubit}")
    return run_experiment(qc_syndrome, backend, shots)


def ask_user_parameters():
    print("\n=== Configuración del experimento Steane ===")

    mode = input("¿Usar simulador? (s/n) [s]: ").strip().lower()
    simulation = (mode != "n")

    qubits = input("Número mínimo de qubits requeridos [7]: ").strip()
    qubits = int(qubits) if qubits else 7

    shots = input("Número de shots [128]: ").strip()
    shots = int(shots) if shots else 128

    error_type = input("Tipo de error (X, Z, Y) [X]: ").strip().upper()
    error_type = error_type if error_type in {"X", "Z", "Y"} else "X"

    error_qubit = input("Qubit a inyectar el error (0–6) [3]: ").strip()
    error_qubit = int(error_qubit) if error_qubit else 3

    return {
        "simulation": simulation,
        "qubits": qubits,
        "shots": shots,
        "error_type": error_type,
        "error_qubit": error_qubit
    }


if __name__ == "__main__":

    params = ask_user_parameters()

    backend = get_backend(
        qubits_required=params["qubits"],
        simulation=params["simulation"]
    )

    run_steane_experiment(
        error_qubit=params["error_qubit"],
        error_type=params["error_type"],
        shots=params["shots"],
        backend=backend
    )
