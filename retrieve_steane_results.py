"""
Script de recuperación de resultados experimentales
Código de Steane – IBM Quantum

Este script NO ejecuta circuitos cuánticos.
Únicamente recupera resultados previamente obtenidos
en hardware real de IBM Quantum, usando job_id públicos.

Requisitos:
- Tener cuenta en IBM Quantum
- Tener configuradas las credenciales localmente
  (qiskit-ibm-runtime)
"""

from qiskit_ibm_runtime import QiskitRuntimeService


# ---------------------------------------------------------------------
# Configuración del servicio IBM Quantum
# ---------------------------------------------------------------------

CHANNEL = "ibm_quantum_platform"
INSTANCE = (
    "crn:v1:bluemix:public:quantum-computing:us-east:"
    "a/71661c35a9384771bbeb8b711ab0320f:"
    "69c0ba29-75f0-44cf-8b36-c6f8a7789bc6::"
)

# Lista de ejecuciones realizadas (job_id)
JOB_IDS = [
    "d64ja83c4tus73fftr0g",
    "d64jc1fs6ggc73fj765g",
    "d64jcsjc4tus73fftut0",
    "d64jelvs6ggc73fj7a0g",
]


def retrieve_job_counts(service, job_id):
    """
    Recupera los counts de un job de IBM Quantum
    siguiendo la API oficial de Qiskit Runtime (Sampler V2).
    """
    print(f"\nRecuperando resultados del job: {job_id}")

    job = service.job(job_id)
    job_result = job.result()

    # En este trabajo se ejecutó un único circuito por job
    pub_result = job_result[0]

    # DataBin con los registros clásicos
    databins = pub_result.data

    # Obtenemos el nombre del registro clásico de forma segura
    creg_names = list(databins.keys())
    if not creg_names:
        raise RuntimeError("No se encontraron registros clásicos en el resultado")

    creg_name = creg_names[0]

    counts = getattr(databins, creg_name).get_counts()

    print(f"Registro clásico utilizado: '{creg_name}'")
    print("Resultados del síndrome (counts):")
    for bitstring, shots in counts.items():
        print(f"  {bitstring} : {shots}")

    return counts



def main():
    print("=== Recuperación de resultados – Código de Steane ===")

    service = QiskitRuntimeService(
        channel=CHANNEL,
        instance=INSTANCE
    )

    for job_id in JOB_IDS:
        retrieve_job_counts(service, job_id)


if __name__ == "__main__":
    main()
