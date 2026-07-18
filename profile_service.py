from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

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
    #1 Disparamos TODO a la vez. submit() no bloquea.

    with ThreadPoolExecutor(max_workers=8) as ex:
        # Pesadas primero: arrancan de inmediato y corren en paralelo
        f_trans = ex.submit(obtener_transaccionalidad,cliente_id,anomes_inicio,anomes_fin)
        f_ach = ex.submit(obtener_ach,cliente_id,anomes_inicio,anomes_fin)
        f_mensual = ex.submit(obtener_mensual,cliente_id,anomes_inicio,anomes_fin)
        f_agencias = ex.submit(obtener_agencias,cliente_id,anomes_inicio,anomes_fin)
        f_causas = ex.submit(obtener_causas,cliente_id,anomes_inicio,anomes_fin)

        #Ligeras:
        f_cliente = ex.submit(obtener_cliente,cliente_id)
        f_cuentas = ex.submit(obtener_cuentas,cliente_id)
        f_firmantes = ex.submit(obtener_cuentas_firmantes,cliente_id)

        #2 Recogemos resultados
        cliente = f_cliente.result()
        cuentas = f_cuentas.result()
        cuentas_firmantes = f_firmantes.result()
        mensual = anomes_fix(f_mensual.result())
        causas = f_causas.result()
        agencias = f_agencias.result()
        transacciones = f_trans.result()
        ach = f_ach.result()
    
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
