import argparse
from datetime import datetime

import pandas as pd

from analisis import (
    anomes_fix,
    generar_grafica_consolidada,
    quetzalizar_montos_agencias,
    quetzalizar_montos_causas,
    tabla_consolidada,
)
from chart import generar_grafica_por_cuentas
from datasources import query_to_df
from pdf import generar_pdf


def obtener_cliente(cliente_id):
    sql = f"""
    select
	clienteId
	, nombre_completo
    , tipo_persona
	, identificacion as dpi
	, nit
	, fecha_nacimiento
	, nacionalidad_1
	, profesion
	, estado_civil
	, direccion_residencia
    , fecha_constitucion
	, email
	, nombre_empleador
	, actividad_empleador
	, egresos_negocio
	, relacion_dependencia
	, tiene_negocio_propio
	, fecha_inicio_relacion
	, fecha_actualizacion
	, es_agente_bam
	, ingresos_adiccionales
	, direccion_oficina
    , coalesce(cast(otras_fuentes_ingresos as integer),0) as otras_fuentes_ingresos
	, coalesce(cast(monto_negocio as integer),0)  as monto_negocio
	, coalesce(cast(ingreso_estimado as integer),0) as ingreso_estimado
    , coalesce(cast(ingresos_reportados as integer),0)  as ingresos_reportados
	, coalesce(cast(monto_extra as integer),0) as monto_extra
    , nit_negocio
	, actividad_economica
	, es_pep
	, es_cpe
	, es_emproblemado
	, embargos_bloqueos
	, colaborador
	, ric
	, estado_cliente_sistema
	, banca
    from proceso_bam_vcum.vis_DimCliente
    where clienteId = '{cliente_id}'
    """
    df = query_to_df(sql)
    if df.empty:
        raise ValueError(
            f"No se encontró información para el cliente con ID {cliente_id}"
        )
    if len(df) > 1:
        raise ValueError(
            f"Se encontró más de un registro para el cliente con ID {cliente_id}"
        )

    return df.iloc[0]


def obtener_cuentas(cliente_id):
    sql = f"""
        select distinct
           	p.cuenta as cuentaid
           	, p.cod_cliente
           	, c.productopasivo
           	, c.monedacuenta
           	, c.estadocuenta
           	, p.rolcliente
            , case
                when p.rolcliente = 'TITULAR' then 1
                when p.rolcliente = 'COTITULAR' then 2
                else 0
             end as tipocliente
        from proceso_bam_vcum.vis_Dim_puente_cliente_pasivos_individual p
        join proceso_bam_vcum.vis_dimcuenta_pasivos_individual c
    	on c.cuentaid = p.cuenta
        where p.cod_cliente = '{cliente_id}'
        and p.rolcliente in ('TITULAR','COTITULAR')
        order by tipocliente asc
    """
    df = query_to_df(sql)

    return df


def obtener_cuentas_firmantes(cliente_id):
    sql = f"""
        select distinct
           	p.cuenta as cuentaid
           	, p.cod_cliente
            , dc.nombre_completo
           	, c.productopasivo
           	, c.estadocuenta
            , t.cod_cliente as titular
        from proceso_bam_vcum.vis_Dim_puente_cliente_pasivos_individual p
        join proceso_bam_vcum.vis_dimcuenta_pasivos_individual c
    	on c.cuentaid = p.cuenta
        left join proceso_bam_vcum.vis_Dim_puente_cliente_pasivos_individual t
        on t.cuenta = p.cuenta
        and t.rolcliente = 'TITULAR'
        join proceso_bam_vcum.vis_dimcliente dc
        on dc.clienteid = t.cod_cliente
        where p.cod_cliente = '{cliente_id}'
          and p.rolcliente in ('FIRMA AUTORIZADA')
    """
    df = query_to_df(sql)

    return df


def obtener_mensual(cliente_id, anomes_inicio, anomes_fin):
    sql = f"""
        select
           	cuentaid
           	, anomes
            , monedacodigotx
           	, sum(montocreditos) as montocreditos
           	, sum(montodebitos) as montodebitos
           	, sum(TxCreditos) as txcreditos
           	, sum(TxDebitos) as txdebitos
        from proceso_bam_vcum.vis_FactTransPasivas_mensual_Individual
        where cuentaid in (
            select
            cuenta
            from proceso_bam_vcum.vis_Dim_puente_cliente_pasivos_individual
            where cod_cliente = '{cliente_id}'
            and rolcliente IN ('TITULAR','COTITULAR')
        )
    	and anomes between {anomes_inicio} and {anomes_fin}
        group by cuentaid,anomes,monedacodigotx
        order by cuentaid,anomes
    """

    df = query_to_df(sql)
    df["pct_creditos"] = df["montocreditos"] / df["montocreditos"].sum() * 100  # pyright: ignore[reportOptionalMemberAccess]

    df["pct_debitos"] = df["montodebitos"] / df["montodebitos"].sum() * 100  # pyright: ignore[reportOptionalMemberAccess]
    return df


# Se hizo cambios a la forma como se obtiene esta informacion por lo que esta consulta ya no es necesaria
# def obtener_causas_debitos(cliente_id, anomes_inicio, anomes_fin):
#     sql = f"""
#         select
#            	f.cuentaid
#             , f.causatransaccion as causatransaccion
#            	, sum(f.montocreditos) as montocreditos
#            	, sum(f.montodebitos) as montodebitos
#            	, sum(f.TxCreditos) as txcreditos
#            	, sum(f.TxDebitos) as txdebitos
#         from proceso_bam_vcum.vis_FactTransPasivas_mensual_Individual f
#         join proceso_bam_vcum.vis_dim_puente_cliente_pasivos_individual p
#             on f.cuentaid = p.cuenta
#         where p.cod_cliente = '{cliente_id}'
#         and p.rolcliente IN ('TITULAR','COTITULAR')
#     	and f.anomes between {anomes_inicio} and {anomes_fin}
#         and f.montodebitos>0
#         group by f.cuentaid,f.causatransaccion
#         order by f.cuentaid,f.causatransaccion
#     """
#     df = query_to_df(sql)

#     df["pct_creditos"] = df["montocreditos"] / df["montocreditos"].sum() * 100  # pyright: ignore[reportOptionalMemberAccess]

#     df["pct_debitos"] = df["montodebitos"] / df["montodebitos"].sum() * 100  # pyright: ignore[reportOptionalMemberAccess]
#     return df


def obtener_agencias(cliente_id, anomes_inicio, anomes_fin):
    sql = f"""
    select
      tpas.cuentaid
      , tpas.anomes
      , tpas.oficina
      , tpas.monedacodigotx
      , tpas.montodebitos
      , tpas.txdebitos
      , tpas.montocreditos
      , tpas.txcreditos
    from proceso_bam_vcum.vis_FactTransPasivas_Agencia tpas
            join proceso_bam_vcum.vis_dim_puente_cliente_pasivos_individual p
                on tpas.cuentaid = p.cuenta
            where p.cod_cliente = '{cliente_id}'
            and p.rolcliente IN ('TITULAR','COTITULAR')
        	  and tpas.anomes between {anomes_inicio} and {anomes_fin}
            order by tpas.cuentaid, tpas.anomes
            """
    df = query_to_df(sql)
    return df


def obtener_causas(cliente_id, anomes_inicio, anomes_fin):
    sql = f"""
        select
           	f.cuentaid
            , f.monedacodigotx
            , f.anomes
            , f.causatransaccion as causatransaccion
           	, f.montocreditos as montocreditos
           	, f.montodebitos as montodebitos
           	, f.txcreditos as txcreditos
           	, f.txdebitos as txdebitos
        from proceso_bam_vcum.vis_FactTransPasivas_mensual_Individual f
        join proceso_bam_vcum.vis_dim_puente_cliente_pasivos_individual p
            on f.cuentaid = p.cuenta
        where p.cod_cliente = '{cliente_id}'
        and p.rolcliente IN ('TITULAR','COTITULAR')
    	and f.anomes between {anomes_inicio} and {anomes_fin}
        order by f.cuentaid,f.causatransaccion
    """
    df = query_to_df(sql)

    df["pct_creditos"] = df["montocreditos"] / df["montocreditos"].sum() * 100  # pyright: ignore[reportOptionalMemberAccess]

    df["pct_debitos"] = df["montodebitos"] / df["montodebitos"].sum() * 100  # pyright: ignore[reportOptionalMemberAccess]
    return df


def obtener_transaccionalidad(cliente_id, anomes_inicio, anomes_fin):
    sql = f"""
    select
       t.cuentaid
      , t.tipooperacion
      , t.monedatransaccion
      , t.canaltransaccion
      , t.cuentadestino
      , p.cod_cliente
      , c.nombre_completo
      , sum(t.montotransaccion) as suma_transaccion
      , count(cod_cliente) as cant_transacciones
    from proceso_bam_vcum.vis_FactTransaccionesPasivas_Individual t
    left join proceso_bam_vcum.vis_Dim_Puente_Cliente_Pasivos_Individual p
	on p.cuenta = t.cuentadestino
	and p.rolcliente = 'TITULAR'
    join proceso_bam_vcum.vis_DimCliente c on p.cod_cliente = c.clienteid
    where CuentaID in (
                        select
                       	cuenta
                        from proceso_bam_vcum.vis_Dim_puente_cliente_pasivos_individual
                        where cod_cliente = '{cliente_id}'
                        and rolcliente IN ('TITULAR','COTITULAR')
                    )
            and from_timestamp(FechaTransaccion,'yyyyMM') between '{anomes_inicio}' and '{anomes_fin}'
            and EstadoTransaccion ='OPERADA'
           	group by  t.CuentaID,t.TipoOperacion, t.MonedaTransaccion,t.CanalTransaccion,t.CuentaDestino,p.cod_cliente, c.nombre_completo
            order by CuentaID,TipoOperacion, sum(t.montotransaccion) desc;
    """
    df = query_to_df(sql)

    return df


def obtener_ach(cliente_id, anomes_inicio, anomes_fin):
    sql = f"""
    select
	f.cuentaid
	, a.tipo_ach
	, a.moneda_desc as moneda
	, a.desc_banco_origen as banco_origen
	, a.cuenta_origen as cuenta_origen
	, a.desc_banco_destino as banco_destino
	, a.cuenta_destino as cuenta_destino
	, a.nombre_cuenta as nombre_destino
	, sum(a.achi_valor) as monto_enviado
	, count(a.cuenta_destino) as cant
    from proceso_bam_vcum.vis_FactTransaccionesPasivas_Individual f
    join proceso_bam_vcum.vis_ext_ach a
	on f.secuenciacore = a.achi_ndnc
	and f.fechatransaccion = a.fecha
    where usuariooperador = 'transach'
	and f.cuentaid in (
                        select
                       	cuenta
                        from proceso_bam_vcum.vis_Dim_puente_cliente_pasivos_individual
                        where cod_cliente = '{cliente_id}'
                        and rolcliente IN ('TITULAR','COTITULAR')
                    )
        and from_timestamp(FechaTransaccion,'yyyyMM') between '{anomes_inicio}' and '{anomes_fin}'
        and EstadoTransaccion ='OPERADA'
     group by f.cuentaid, f.tipooperacion,a.tipo_ach,a.cuenta_origen,a.moneda_desc,a.desc_banco_origen,a.desc_banco_destino,a.cuenta_destino,a.nombre_cuenta
     order by f.cuentaid, f.tipooperacion,sum(a.achi_valor) desc

    """
    df = query_to_df(sql)

    return df


def obtener_internacional(cliente_id, anomes_inicio, anomes_fin):
    sql = f"""
    select
       	op_cod_cliente
       	, pn_num_cuenta
       	, pn_beneficiario
       	, pn_num_cheque
       	, pn_titular_cuenta
       	, sum(pn_monto2) as suma_monto
       	, count(pn_cod_operacion) as cant
    from proceso_bam_vcum.visext_internacional
    where op_cod_cliente = {cliente_id}
    and REPLACE(SUBSTR(op_fecha_creacion, 1, 7), '-', '')
            BETWEEN '{anomes_inicio}' and '{anomes_fin}'
    group by op_cod_cliente, pn_num_cuenta,pn_beneficiario,pn_num_cheque,pn_titular_cuenta
    order by sum(pn_monto2) desc;
    """
    df = query_to_df(sql)

    return df

def alertas_empleado(cliente_id):
        sql = f"""
        SELECT DISTINCT
            cod_empleado_base,
         cod_cliente,
         categoria_persona,
         parentesco,
         nombre_completo,
         cui,
         tipo_documento,
         profesion,
         telefono,
         correo,
         direccion,
         empresa,
         division,
         unidad,
         puesto,
         jefe_directo,
         anos_antiguedad,
         fecha_de_ingreso,
         ingreso_mensual,
         tipo_ingreso,
         tipo_producto,
         numero_producto,
         categoria,
         descripcion_producto,
         agencia,
         fecha_apertura,
         estado,
         detalle_estado,
         limite_credito_tc,
         saldo_actual_tc,
         saldo_disponible_tc,
         saldo_cuenta,
         numero_caso,
         canal_recepcion_denuncia,
         clasificacion_denuncia,
         fecha_recepcion,
         fecha_asignacion,
         contexto_denuncia,
         operador,
         jornada,
         zona,
         vicepresidencia,
         socio_estrategico,
         usuario_cobis,
         consecutivo_cobis,
         usuario_bancolombia,
         moneda,
         moneda_tarjeta,
         profesion_actividad_economica,
         productos_activos,
         edad,
         llave_busqueda
        FROM proceso_bam_vcum.`1mtfi_en_perfilado_denuncias_maestro`
        WHERE cod_cliente = {cliente_id}
        AND numero_producto <> 'NO DISPONIBLE'
        AND moneda_tarjeta <> 'USD'
        ORDER BY
         CASE WHEN parentesco = 'TITULAR' THEN 1 ELSE 2 END,
         parentesco,
         tipo_producto;
        """
        df = query_to_df(sql)
        if df.empty:
            return None
        try:
            return df
        except Exception:
            return None

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("--Id_Cliente", required=True)
    parser.add_argument("--inicio", required=True)
    parser.add_argument("--fin", required=True)
    args = parser.parse_args()

    fecha_inicio = datetime.strptime(args.inicio, "%Y-%m-%d")
    fecha_fin = datetime.strptime(args.fin, "%Y-%m-%d")

    anomes_inicio = int(fecha_inicio.strftime("%Y%m"))
    anomes_fin = int(fecha_fin.strftime("%Y%m"))

    alertas =alertas_empleado(args.Id_Cliente)
    print(alertas)
    cliente = obtener_cliente(args.Id_Cliente)
    ing_extra = cliente["monto_extra"] or 0
    ing_ofi = cliente["ingresos_reportados"] or 0
    ing_estimado = cliente["ingreso_estimado"] or 0
    ing_empresa = cliente["monto_negocio"] or 0
    cuentas_df = obtener_cuentas(args.Id_Cliente)
    cuentas = cuentas_df.to_dict(orient="records")
    cuentas_firmante_df = obtener_cuentas_firmantes(args.Id_Cliente)
    cuentas_firmante = cuentas_firmante_df.to_dict(orient="records")
    mensual_raw = obtener_mensual(args.Id_Cliente, anomes_inicio, anomes_fin)
    mensual = anomes_fix(mensual_raw)
    causas_sin_quetzalizar = obtener_causas(args.Id_Cliente, anomes_inicio, anomes_fin)
    causas_transacciones = quetzalizar_montos_causas(causas_sin_quetzalizar)
    agencias_usadas = obtener_agencias(args.Id_Cliente, anomes_inicio, anomes_fin)
    quetzalizar_agencias = quetzalizar_montos_agencias(agencias_usadas)

    grafica_buffers = generar_grafica_por_cuentas(
        mensual,ing_extra,ing_ofi,ing_estimado,ing_empresa
     )
    filename = "Perfil_cliente.pdf"

    tabla_general = tabla_consolidada(mensual)
    grafica_consolidada_buffer = generar_grafica_consolidada(
        tabla_general, ing_extra, ing_ofi, ing_estimado,ing_empresa
    )

    tabla_transacciones = obtener_transaccionalidad(
        args.Id_Cliente, anomes_inicio, anomes_fin
    )

    tabla_ach = obtener_ach(args.Id_Cliente, anomes_inicio, anomes_fin)
   ## tabla_internacional = obtener_internacional(
     #   args.Id_Cliente, anomes_inicio, anomes_fin
    #)

    # df_detalle = obtener_transacciones_detalle(
    #     args.Id_Cliente,
    #     fecha_inicio.strftime("%Y-%m-%d"),
    #     fecha_fin.strftime("%Y-%m-%d"),
    # )
    generar_pdf(
        filename=filename,
        cliente=cliente,
        cuentas=cuentas,
        cuentas_firmantes=cuentas_firmante,
        mensual=mensual,
        tabla_consolidada=tabla_general,
        causas_trans=causas_transacciones,
        grafica_buffer=grafica_buffers,
        grafica_consolidada=grafica_consolidada_buffer,
        agencias_usadas=quetzalizar_agencias,
        tabla_transaccion=tabla_transacciones,
        tabla_ach=tabla_ach,
        fecha_rep_inicio= fecha_inicio,
        fecha_rep_fin= fecha_fin,
    )
    print("Reporte generado exitosamente")


if __name__ == "__main__":
    main()
