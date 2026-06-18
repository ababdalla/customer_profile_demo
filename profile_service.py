from datetime import datetime

from generar_reporte import (
    obtener_cliente,
    obtener_cuentas,
    obtener_cuentas_firmantes,
    obtener_mensual,
    obtener_causas,
    obtener_agencias,
    obtener_transaccionalidad,
    obtener_ach,
)
from analisis import (
    anomes_fix,
    tabla_consolidada,
    quetzalizar_montos_causas,
    quetzalizar_montos_agencias,
)


def build_customer_profile(cliente_id: str, fecha_inicio: datetime, fecha_fin: datetime):
    anomes_inicio = int(fecha_inicio.strftime("%Y%m"))
    anomes_fin = int(fecha_fin.strftime("%Y%m"))

    cliente = obtener_cliente(cliente_id)
    cuentas = obtener_cuentas(cliente_id)
    cuentas_firmantes = obtener_cuentas_firmantes(cliente_id)

    mensual_raw = obtener_mensual(cliente_id, anomes_inicio, anomes_fin)
    mensual = anomes_fix(mensual_raw)

    causas_raw = obtener_causas(cliente_id, anomes_inicio, anomes_fin)
    causas = quetzalizar_montos_causas(causas_raw)

    agencias_raw = obtener_agencias(cliente_id, anomes_inicio, anomes_fin)
    agencias = quetzalizar_montos_agencias(agencias_raw)

    transacciones = obtener_transaccionalidad(cliente_id, anomes_inicio, anomes_fin)
    ach = obtener_ach(cliente_id, anomes_inicio, anomes_fin)
    consolidado = tabla_consolidada(mensual)

    total_creditos = consolidado["montocreditos_gtq"].sum()
    total_debitos = consolidado["montodebitos_gtq"].sum()

    return {
        "cliente": cliente,
        "cuentas": cuentas,
        "cuentas_firmantes": cuentas_firmantes,
        "mensual": mensual,
        "consolidado": consolidado,
        "causas": causas,
        "agencias": agencias,
        "transacciones": transacciones,
        "ach": ach,
        "kpis": {
            "total_creditos": total_creditos,
            "total_debitos": total_debitos,
            "flujo_neto": total_creditos - total_debitos,
            "cantidad_cuentas": len(cuentas),
        },
    }
