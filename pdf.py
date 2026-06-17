# pdf.py
import datetime
import hashlib
from datetime import datetime
from re import L
from tkinter import TclError

from matplotlib.backend_tools import ToolSetCursor
#from numpy.typing import _32Bit
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generar_pdf(
    filename,
    cliente,
    cuentas,
    cuentas_firmantes,
    mensual,
    causas_trans,
    grafica_buffer,
    grafica_consolidada,
    tabla_consolidada,
    agencias_usadas,
    tabla_transaccion,
    tabla_ach,
    fecha_rep_inicio,
    fecha_rep_fin,
):

    doc = SimpleDocTemplate(
        filename,
        pagesize=landscape(A4),
        rightMargin=15,
        leftMargin=15,
        topMargin=15,
        bottomMargin=15,
    )

    elements = []
    styles = _build_styles()

    add_header(elements, styles, cliente)
    add_metadata(elements, styles, cliente,fecha_rep_fin,fecha_rep_inicio)
    add_identificacion_cuentas(
        elements,
        styles,
        cliente,
        cuentas,
        cuentas_firmantes,
        grafica_consolidada,
        tabla_consolidada,
    )
    # add_kyc(elements, styles, cliente)
    # add_cuentas(elements, styles, cuentas, cuentas_firmantes)

    for cuenta in cuentas:
        cuenta_id = str(cuenta["cuentaid"]).strip()
        add_cuenta_section(
            elements,
            styles,
            cuenta_id,
            mensual,
            causas_trans,
            grafica_buffer,
            agencias_usadas,
            tabla_transaccion,
            tabla_ach,
        )

    doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)


def _build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SectionTitle", fontSize=14, fontName="Helvetica-Bold", spaceAfter=10
        )
    )
    styles.add(ParagraphStyle(name="NormalSmall", fontSize=9, spaceAfter=4))
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["Normal"],
            fontSize=7,
            leading=9,
            spaceBefore=0,
            spaceAfter=0,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["Normal"],
            fontSize=8,
            leading=10,
            textColor=colors.black,
            spaceBefore=0,
            spaceAfter=0,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Cell",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=6,
            leading=9,
            wordWrap="CJK",  # <-- Necesario para cortar texto sin espacios
            spaceBefore=0,
            spaceAfter=0,
        )
    )
    return styles


def _default_table_style():
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.gray),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]
    )

    # def add_kyc(elements, styles, cliente):
    #     elements.append(Paragraph("Información KYC", styles["SectionTitle"]))

    #     data = [
    #         ["Nombre", cliente["nombre_completo"], "PEP", str(cliente["es_cliente_pep"])],
    #         [
    #             "Actividad Económica",
    #             cliente["actividad_economica"],
    #             "CPE",
    #             str(cliente["es_cliente_cpe"]),
    #         ],
    #         [
    #             "Ingresos Reportados",
    #             str(cliente["ingresos_reportados"]),
    #             "Estado Cliente",
    #             cliente["estado_cliente_sistema"],
    #         ],
    #     ]

    #     table = Table(data, colWidths=[150, 300, 100, 200])

    #     table.setStyle(
    #         TableStyle(
    #             [
    #                 ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    #                 ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
    #             ]
    #         )
    #     )

    # elements.append(table)
    # elements.append(Spacer(1, 0.3 * inch))


def add_footer(canvas, doc):
    canvas.setFont("Helvetica", 8)
    canvas.drawString(30, 15, "Documento generado automáticamente")
    canvas.drawRightString(800, 15, f"Página {doc.page}")


def add_identificacion_cuentas(
    elements,
    styles,
    cliente,
    cuentas,
    cuentas_firmantes,
    grafica_consolidada,
    tabla_consolidada,
):
    # ---Info general cliente---
    # Tratamiento a variables
   

    ingresos_reportado = cliente['ingresos_reportados'] + cliente['monto_negocio'] + cliente["monto_extra"]
    tabla_gen = None
    # Información si el cliente es Individual
    data_gen = [
        ["DPI", cliente.get("dpi", "")],
        ["NIT", cliente.get("nit", "")],
        ["Fecha inicio relación", str(cliente.get("fecha_inicio_relacion", ""))],
        ["Fecha Nacimiento", str(cliente.get("fecha_nacimiento", ""))],
        ["Estado Civil", cliente.get("estado_civil", "")],
        ["Correo Electronico",cliente.get('email','')],
        ["Profesión", cliente.get("profesion", "")],
        ["¿Es empleado?", cliente.get("relacion_dependencia", "")],
        ["¿Tiene empresa?", cliente.get("tiene_negocio_propio", "")],
        [
            "Actividad Económica",
            Paragraph(cliente.get("actividad_economica", ""), styles["Cell"]),
        ],
        ["CPE", str(cliente.get("es_cpe", ""))],
        ["Ingresos Reportados", f"Q {ingresos_reportado:,.0f}"],
        [
            "Ingresos Adicionales",
            Paragraph(cliente.get("ingresos_adiccionales") or "", styles["Cell"]),
        ],
        ["Egresos negocio", cliente.get("egresos_negocio", "0")],
        ["Estado Cliente", cliente.get("estado_cliente_sistema", "")],
        ["RIC", cliente.get("ric", "")],
        ["Fecha actualización", cliente.get("fecha_actualizacion", "")],
    ]
    if cliente.get("ingreso_estimado"):
        data_gen.append(["Ingresos estimados", cliente.get("ingreso_estimado",0)])
    if cliente.get("ingresos_adiccionales"):
        data_gen.append(["Ingresos adicionales", cliente.get("ingresos_adiccionales" ,0)])
    # Información si el cliente es Jurídico
    
    data_gen_juris = [
        ["NIT", cliente.get("nit", "")],
        ["Fecha inicio relación", str(cliente.get("fecha_inicio_relacion", ""))],
        ["Fecha Constitución", cliente.get('fecha_constitucion','')],
        ["Correo electronico",cliente.get('email','')],
        [
            "Actividad Económica",
            Paragraph(cliente.get("actividad_economica", ""), styles["Cell"]),
        ],
        ["CPE", str(cliente.get("es_cpe", ""))],
        ["Ingresos Reportados", ingresos_reportado],
        ["Egresos negocio", cliente.get("egresos_negocio", "0")],
        ["Estado Cliente", cliente.get("estado_cliente_sistema", "")],
        ["RIC", cliente.get("ric", "")],
        ["Fecha actualización", cliente.get("fecha_actualizacion", "")],
    ]
    if cliente.get("ingreso_estimado"):
        data_gen_juris.append(["Ingresos estimados", cliente.get("ingreso_estimado",0)])
    
    if cliente.get("ingresos_adiccionales"):
        data_gen_juris.append(["Ingresos adicionales", cliente.get("ingresos_adiccionales" ,0)])

    if cliente['tipo_persona'] == 'INDIVIDUAL':
        tabla_gen = Table(data_gen, colWidths=[90, 150])
    elif cliente['tipo_persona'] == 'JURIDICO':
        tabla_gen = Table(data_gen_juris, colWidths=[90,150])
    else:
        raise ValueError(
            f"tipo_persona desconocido:{cliente['tipo_persona']}"
        )

    tabla_gen.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ]
        )
    )
    tabla_tit = None
    data_tit = [["Cuenta", "Producto", "Moneda", "Estado", "Rol"]]

    for c in cuentas:
        data_tit.append(
            [
                c["cuentaid"],
                c["productopasivo"],
                c["monedacuenta"],
                c["estadocuenta"],
                "TITULAR",
            ]
        )
    tabla_tit = Table(data_tit)
    tabla_tit.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ]
        )
    )
    tabla_completa_cuentas = None
    data_con = [
        [
            "Año",
            "Mes",
            "Tx",
            "Creditos",
            "%Creditos",
            "Tx",
            "Debitos",
            "%Debitos",
        ]
    ]

    for _, row in tabla_consolidada.iterrows():
        data_con.append(
            [
                f"{row['year']:.0f}",
                f"{row['month']:.0f}",
                f"{row['txcreditos']:.0f}",
                f"{row['montocreditos_gtq']:,.2f}",
                f"{row['pct_creditos']:,.2f}%",
                f"{row['txdebitos']:.0f}",
                f"{row['montodebitos_gtq']:,.2f}",
                f"{row['pct_debitos']:,.2f}%",
            ]
        )

    total_txcreditos_consolidada = tabla_consolidada["txcreditos"].sum()
    total_creditos_consolidada = tabla_consolidada["montocreditos_gtq"].sum()
    total_pctcreditos_consolidada = tabla_consolidada["pct_creditos"].sum()
    total_txdebitos_consolidada = tabla_consolidada["txdebitos"].sum()
    total_debitos_consolidada = tabla_consolidada["montodebitos_gtq"].sum()
    total_pctdebitos_consolidada = tabla_consolidada["pct_debitos"].sum()

    fila_totales = [
        "",
        "TOTAL",
        total_txcreditos_consolidada,
        f"{total_creditos_consolidada:,.2f}",
        f"{total_pctcreditos_consolidada:,.0f}%",
        total_txdebitos_consolidada,
        f"{total_debitos_consolidada:,.2f}",
        f"{total_pctdebitos_consolidada:,.0f}%",
    ]
    data_con.append(fila_totales)

    tabla_completa_cuentas = Table(data_con)
    last_row_idx_compilado = len(data_con) - 1
    tabla_completa_cuentas.setStyle(
        TableStyle(
            [
                # Encabezado
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Celdas generales
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                # Alineación: primera columna a la izquierda, numéricas a la derecha
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                # Fila de totales resaltada
                (
                    "BACKGROUND",
                    (0, last_row_idx_compilado),
                    (-1, last_row_idx_compilado),
                    colors.whitesmoke,
                ),
                (
                    "FONTNAME",
                    (0, last_row_idx_compilado),
                    (-1, last_row_idx_compilado),
                    "Helvetica-Bold",
                ),
            ]
        )
    )
    right_column = [
        tabla_tit,
        Spacer(1, 10),
        Paragraph("<b>Tabla consolidada (Montos en GTQ) </b>", styles["Normal"]),
        Spacer(1, 10),
        tabla_completa_cuentas,
    ]
    # Tabla_internacional
    #df_internacional = tabla_internacional:
    #df_internacional = df_internacional.sort_values("suma_monto", ascending=False).head( 10)
    #tabla_internacional = None
    #if not df_internacional.empty:
     #   data_ach_c = [["Cuenta", "Beneficiario", "Cheque", "Titular", "Tx", "Monto"]]

    #    for _, row in df_internacional.iterrows():
    #        data_ach_c.append(
    #            [
    #                row["pn_num_cuenta"],
    #                row["pn_beneficiario"],
    #                row["pn_num_cheque"],
    #                row["pn_titular_cuenta"],  # pyright: ignore[reportArgumentType]
    #                row["cant"],
    #                f"{row['suma_monto']:,.2f}",
    #            ]
    #        )

    #    tabla_internacional = Table(data_ach_c, colWidths=[60, 120, 40, 60, 35, 60])
    #    tabla_internacional.setStyle(
    #        [
    #            # Encabezado
    #            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    #            ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
    #            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Celdas generales
    #            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    #            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
    #            ("FONTSIZE", (0, 0), (-1, -1), 6),
                # Alineación: primera columna a la izquierda, numéricas a la derecha
    #            ("ALIGN", (0, 1), (0, -1), "LEFT"),
    #            ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
    #        ]
    #    )
    if cuentas_firmantes:
        data_firm = [["Cuenta", "Productos", "Estado", "Consecutivo", "Nombre Titular"]]
        tabla_firm = None
        img = None
        img = Image(grafica_consolidada)
        maxW, maxH = 345, 700
        img._restrictSize(maxW, maxH)  # pyright: ignore[reportAttributeAccessIssue]
        img.hAlign = "CENTER"

        for c in cuentas_firmantes:
            data_firm.append(
                [
                    c["cuentaid"],
                    c["productopasivo"],
                    c["estadocuenta"],
                    c["titular"],
                    c["nombre_completo"],
                ]
            )

        tabla_firm = Table(data_firm)
        tabla_firm.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ]
            )
        )
        right_column_cuentas = [
            tabla_tit,
            Spacer(1, 10),
            Paragraph("<b>Información Cuentas Firmante</b>", styles["Normal"]),
            Spacer(1, 10),
            tabla_firm,
        ]
        bloque_superior = Table(
            [
                [
                    Paragraph("<b>Información Cliente</b>", styles["Normal"]),
                    Paragraph("<b>Información Cuentas Titular</b>", styles["Normal"]),
                ],
                [tabla_gen, right_column_cuentas],
            ],
            colWidths=[350, 350],
        )
        bloque_superior.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        elements.append(bloque_superior)
        elements.append(PageBreak())
        bloque_inferior = Table(
            [
                [
                    Paragraph("<b>Carta de control movimientos</b>", styles["Normal"]),
                    Paragraph(
                        "<b>Cuentas consolidadas (Montos en GTQ)</b>", styles["Normal"]
                    ),
                ],
                [img, tabla_completa_cuentas],
            ],
            colWidths=[350, 350],
        )
        bloque_superior.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        elements.append(bloque_inferior)
        elements.append(Spacer(1, 0.05 * inch))
        elements.append(
            Paragraph("<b>Tabla Internacional Cliente</b>", styles["Normal"]),
        )
        #elements.append(tabla_internacional)
        # elements.append(PageBreak())
    else:
        bloque_superior = Table(
            [
                [
                    Paragraph("<b>Información Cliente</b>", styles["Normal"]),
                    Paragraph("<b>Información Cuentas Titular</b>", styles["Normal"]),
                ],
                [tabla_gen, right_column],
            ],
            colWidths=[350, 350],
        )
        bloque_superior.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
        elements.append(bloque_superior)
        img = None
        img = Image(grafica_consolidada, width=500, height=300)
        elements.append(img)
    elements.append(PageBreak())


def add_header(elements, styles, cliente):
    # logo = Image("static/logo.png", width=2 * inch, height=0.5 * inch)

    title = Paragraph(f"<b>{cliente['nombre_completo']}</b>", styles["Title"])
    # header_table = Table([[logo, title]], colWidths=[200, 500])
    elements.append(title)
    elements.append(Spacer(1, 0.05 * inch))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Spacer(1, 0.05 * inch))


def add_metadata(elements, styles, cliente,fecha_rep_inicio,fecha_rep_fin):
    from datetime import datetime
    fecha_inicio_str = fecha_rep_fin.strftime("%d-%m-%Y")
    fecha_fin_str = fecha_rep_inicio.strftime("%d-%m-%Y")
    fecha_reporte = f"{fecha_inicio_str} al {fecha_fin_str}"
    data = [
        [
            "FECHA GENERACIÓN",
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "CONSECUTIVO",
            cliente["clienteid"],
            "FECHA REPORTE",
            fecha_reporte,
        ],
    ]
    table = Table(data, colWidths=[100, 100,70, 50,80,100])
    table.setStyle(_default_table_style())
    elements.append(table)
    elements.append(Spacer(1, 0.05 * inch))


# def add_cuentas(elements, styles, cuentas, cuentas_firmantes):
#     elements.append(Paragraph("Productos/Cuentas", styles["SectionTitle"]))
#     data = [["Cuenta", "Producto", "Moneda", "Estado", "Rol"]]
#     for c in cuentas:
#         data.append(
#             [
#                 c["cuentaid"],
#                 c["productopasivo"],
#                 c["monedacuenta"],
#                 c["estadocuenta"],
#                 "TITULAR",
#             ]
#         )
#     table = Table(data)
#     table.setStyle(_default_table_style())

#     elements.append(table)
#     elements.append(Spacer(1, 0.2 * inch))

#     if cuentas_firmantes:
#         elements.append(Paragraph("Cuentas como firmante", styles["SectionTitle"]))

#         data_firm = [["Cuenta", "Productos", "Estado", "Consecutivo", "Nombre Titular"]]

#         for c in cuentas_firmantes:
#             data_firm.append(
#                 [
#                     c["cuentaid"],
#                     c["productopasivo"],
#                     c["estadocuenta"],
#                     c["cod_cliente"],
#                     c["nombre_completo"],
#                 ]
#             )
#         table_firm = Table(data_firm)
#         table_firm.setStyle(_default_table_style())
#         elements.append(table_firm)


def add_cuenta_section(
    elements,
    styles,
    cuenta_id,
    mensual,
    causas_trans,
    grafica_buffer,
    agencias_usadas,
    tabla_transaccion,
    tabla_ach,
):

    # Grafica
    img = None
    if cuenta_id in grafica_buffer:
        img = Image(grafica_buffer[cuenta_id])
        maxW, maxH = 400, 350
        img._restrictSize(maxW, maxH)  # pyright: ignore[reportAttributeAccessIssue]
        img.hAlign = "CENTER"

    # Tabla mensual filtrada
    df_mensual = mensual[mensual["cuentaid"] == cuenta_id]

    tabla_mensual = None
    if not df_mensual.empty:
        # Codigo proporcinado por Copilot, revisar que cols numericas no tengan NAN
        cols_numericas = ["txcreditos", "montocreditos", "txdebitos", "montodebitos"]
        df_mensual[cols_numericas] = df_mensual[cols_numericas].fillna(0)
        df_mensual["pct_creditos_cuenta"] = (
            df_mensual["montocreditos"] / df_mensual["montocreditos"].sum() * 100
        )
        df_mensual["pct_debitos_cuenta"] = (
            df_mensual["montodebitos"] / df_mensual["montodebitos"].sum() * 100
        )
        data_m = [
            [
                "Año",
                "Mes",
                "Tx",
                "Créditos",
                "%Créditos",
                "Tx",
                "Débitos",
                "%Débitos",
            ]
        ]

        for _, row in df_mensual.iterrows():
            data_m.append(
                [
                    row["year"],
                    row["month"],
                    row["txcreditos"],
                    f"{row['montocreditos']:,.2f}",
                    f"{row['pct_creditos_cuenta']:,.2f}%",
                    row["txdebitos"],
                    f"{row['montodebitos']:,.2f}",
                    f"{row['pct_debitos_cuenta']:,.2f}%",
                ]
            )

        total_tx_creditos = df_mensual["txcreditos"].sum()
        total_monto_creditos = df_mensual["montocreditos"].sum()
        total_pctcreditos = df_mensual["pct_creditos_cuenta"].sum()
        total_tx_debitos = df_mensual["txdebitos"].sum()
        total_monto_debitos = df_mensual["montodebitos"].sum()
        total_pctdebitos = df_mensual["pct_debitos_cuenta"].sum()

        fila_totales = [
            "",
            "TOTAL",
            total_tx_creditos,
            f"{total_monto_creditos:,.2f}",
            f"{total_pctcreditos:,.2f}%",
            total_tx_debitos,
            f"{total_monto_debitos:,.2f}",
            f"{total_pctdebitos:,.2f}%",
        ]
        data_m.append(fila_totales)

        tabla_mensual = Table(data_m, colWidths=[30, 30, 30, 60, 45, 30, 60, 45])

        last_row_idx = len(data_m) - 1  # Índice de la fila de totales
        tabla_mensual.setStyle(
            [
                # Encabezado
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Celdas generales
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                # Alineación: primera columna a la izquierda, numéricas a la derecha
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                # Fila de totales resaltada
                (
                    "BACKGROUND",
                    (0, last_row_idx),
                    (-1, last_row_idx),
                    colors.whitesmoke,
                ),
                ("FONTNAME", (0, last_row_idx), (-1, last_row_idx), "Helvetica-Bold"),
            ]
        )

    # ----Contenedor superior ---

    if img and tabla_mensual:
        bloque_superior = Table(
            [[img, tabla_mensual]], colWidths=[400, 312], hAlign="CENTER"
        )
        bloque_superior.setStyle(
            TableStyle(
                [
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "TOP",
                    ),  # centra verticalmente imagen vs tabla
                    ("ALIGN", (0, 0), (0, 0), "CENTER"),  # centra la imagen en su celda
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    # Si quieres ver el contenedor mientras calibras:
                    # ("GRID", (0, 0), (-1, -1), 0.25, colors.pink),
                ]
            )
        )

        elements.append(bloque_superior)

    # Agencias usadas
    # ## Agencias creditos
    df_agencias_creditos = agencias_usadas[
        (agencias_usadas["txcreditos"] > 0) & (agencias_usadas["cuentaid"] == cuenta_id)
    ]
    df_agencias_creditos["pct_creditos_cuenta"] = (
        df_agencias_creditos["montocreditos"]
        / df_agencias_creditos["montocreditos"].sum()
        * 100
    )
    df_agencias_creditos = df_agencias_creditos.sort_values(
        "pct_creditos_cuenta", ascending=False
    )
    tabla_agencias_creditos = None

    if not df_agencias_creditos.empty:
        cols_numericas_a_c = ["txcreditos", "montocreditos", "pct_creditos_cuenta"]
        df_agencias_creditos[cols_numericas_a_c] = df_agencias_creditos[
            cols_numericas_a_c
        ].fillna(0)

        data_a_c = [["Agencia", "Tx", "Monto", "%Monto"]]

        for _, row in df_agencias_creditos.iterrows():
            data_a_c.append(
                [
                    Paragraph(row["oficina"], styles["Cell"]),  # pyright: ignore[reportArgumentType]
                    row["txcreditos"],
                    f"{row['montocreditos']:,.2f}",
                    f"{row['pct_creditos_cuenta']:,.2f}%",
                ]
            )
        total_tx_a_c = df_agencias_creditos["txcreditos"].sum()
        total_monto_a_c = df_agencias_creditos["montocreditos"].sum()
        total_pct_a_c = df_agencias_creditos["pct_creditos_cuenta"].sum()

        fila_totales_a_c = [
            "TOTAL",
            total_tx_a_c,
            f"{total_monto_a_c:,.2f}",
            f"{total_pct_a_c:,.2f}%",
        ]
        data_a_c.append(fila_totales_a_c)
        tabla_agencias_creditos = Table(data_a_c, colWidths=[90, 40, 60, 40])
        last_row_idx_a_c = len(data_a_c) - 1  # Índice de la fila de totales
        tabla_agencias_creditos.setStyle(
            [
                # Encabezado
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Celdas generales
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                # Alineación: primera columna a la izquierda, numéricas a la derecha
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                # Fila de totales resaltada
                (
                    "BACKGROUND",
                    (0, last_row_idx_a_c),
                    (-1, last_row_idx_a_c),
                    colors.whitesmoke,
                ),
                (
                    "FONTNAME",
                    (0, last_row_idx_a_c),
                    (-1, last_row_idx_a_c),
                    "Helvetica-Bold",
                ),
            ]
        )

    ### Agencias debitos
    df_agencias_debitos = agencias_usadas[
        (agencias_usadas["txdebitos"] > 0) & (agencias_usadas["cuentaid"] == cuenta_id)
    ]
    df_agencias_debitos["pct_debitos_cuenta"] = (
        df_agencias_debitos["montodebitos"]
        / df_agencias_debitos["montodebitos"].sum()
        * 100
    )
    df_agencias_debitos = df_agencias_debitos.sort_values(
        "pct_debitos_cuenta", ascending=False
    )
    tabla_agencias_debitos = None

    if not df_agencias_debitos.empty:
        cols_numericas_a_c = ["txdebitos", "montodebitos", "pct_debitos_cuenta"]
        df_agencias_debitos[cols_numericas_a_c] = df_agencias_debitos[
            cols_numericas_a_c
        ].fillna(0)

        data_a_d = [["Agencia", "Tx", "Monto", "%Monto"]]

        for _, row in df_agencias_debitos.iterrows():
            data_a_d.append(
                [
                    Paragraph(row["oficina"], styles["Cell"]),  # pyright: ignore[reportArgumentType]
                    row["txdebitos"],
                    f"{row['montodebitos']:,.2f}",
                    f"{row['pct_debitos_cuenta']:,.2f}%",
                ]
            )
        total_tx_a_d = df_agencias_debitos["txdebitos"].sum()
        total_monto_a_d = df_agencias_debitos["montodebitos"].sum()
        total_pct_a_d = df_agencias_debitos["pct_debitos_cuenta"].sum()

        fila_totales_a_c = [
            "TOTAL",
            total_tx_a_d,
            f"{total_monto_a_d:,.2f}",
            f"{total_pct_a_d:,.2f}%",
        ]
        data_a_d.append(fila_totales_a_c)
        tabla_agencias_debitos = Table(data_a_d, colWidths=[90, 40, 60, 40])
        last_row_idx_a_d = len(data_a_d) - 1  # Índice de la fila de totales
        tabla_agencias_debitos.setStyle(
            [
                # Encabezado
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Celdas generales
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                # Alineación: primera columna a la izquierda, numéricas a la derecha
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                # Fila de totales resaltada
                (
                    "BACKGROUND",
                    (0, last_row_idx_a_d),
                    (-1, last_row_idx_a_d),
                    colors.whitesmoke,
                ),
                (
                    "FONTNAME",
                    (0, last_row_idx_a_d),
                    (-1, last_row_idx_a_d),
                    "Helvetica-Bold",
                ),
            ]
        )

    # Causas creditos
    df_creditos = causas_trans[
        (causas_trans["cuentaid"] == cuenta_id) & (causas_trans["txcreditos"] > 0)
    ]
    df_creditos = df_creditos.sort_values("montocreditos", ascending=False)
    tabla_creditos = None
    if not df_creditos.empty:
        cols_numericas_c = ["txcreditos", "montocreditos"]
        df_creditos[cols_numericas_c] = df_creditos[cols_numericas_c].fillna(0)
        df_creditos["pct_creditos_cuenta"] = (
            df_creditos["montocreditos"] / df_creditos["montocreditos"].sum() * 100
        )

        data_c = [["Tipo Transacción", "Tx", "Monto", "% Monto"]]

        for _, row in df_creditos.iterrows():
            data_c.append(
                [
                    Paragraph(row["causatransaccion"], styles["Cell"]),  # pyright: ignore[reportArgumentType]
                    row["txcreditos"],
                    f"{row['montocreditos']:,.2f}",
                    f"{row['pct_creditos_cuenta']:,.2f}%",
                ]
            )

        total_tx = df_creditos["txcreditos"].sum()
        total_monto = df_creditos["montocreditos"].sum()
        total_pctcreditos = df_creditos["pct_creditos_cuenta"].sum()

        fila_totales = [
            "TOTAL",
            total_tx,
            f"{total_monto:,.2f}",
            f"{total_pctcreditos:,.2f}%",
        ]
        data_c.append(fila_totales)

        tabla_creditos = Table(data_c, colWidths=[150, 40, 60, 40])
        last_row_idx_c = len(data_c) - 1  # Índice de la fila de totales
        tabla_creditos.setStyle(
            [
                # Encabezado
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Celdas generales
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                # Alineación: primera columna a la izquierda, numéricas a la derecha
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                # Fila de totales resaltada
                (
                    "BACKGROUND",
                    (0, last_row_idx_c),
                    (-1, last_row_idx_c),
                    colors.whitesmoke,
                ),
                (
                    "FONTNAME",
                    (0, last_row_idx_c),
                    (-1, last_row_idx_c),
                    "Helvetica-Bold",
                ),
            ]
        )

    # Causas Debitos
    df_debitos = causas_trans[
        (causas_trans["cuentaid"] == cuenta_id) & (causas_trans["txdebitos"] > 0)
    ]
    df_debitos = df_debitos.sort_values("montodebitos", ascending=False).head(9)
    tabla_debitos = None
    if not df_debitos.empty:
        cols_numericas_d = ["txdebitos", "montodebitos"]
        df_debitos[cols_numericas_d] = df_debitos[cols_numericas_d].fillna(0)
        df_debitos["pct_debitos_cuenta"] = (
            df_debitos["montodebitos"] / df_debitos["montodebitos"].sum() * 100
        )
        data_d = [["Tipo Transacción", "Tx", "Monto", "% Monto"]]

        for _, row in df_debitos.iterrows():
            data_d.append(
                [
                    Paragraph(row["causatransaccion"], styles["Cell"]),  # pyright: ignore[reportArgumentType]
                    row["txdebitos"],
                    f"{row['montodebitos']:,.2f}",
                    f"{row['pct_debitos_cuenta']:,.2f}%",
                ]
            )
        total_tx_d = df_debitos["txdebitos"].sum()
        total_monto_d = df_debitos["montodebitos"].sum()
        total_pctdebitos = df_debitos["pct_debitos_cuenta"].sum()

        fila_totales = [
            "TOTAL",
            total_tx_d,
            f"{total_monto_d:,.2f}",
            f"{total_pctdebitos:,.2f}%",
        ]
        data_d.append(fila_totales)
        tabla_debitos = Table(data_d, colWidths=[150, 40, 60, 40])
        last_row_idx_d = len(data_d) - 1  # Índice de la fila de totales
        tabla_debitos.setStyle(
            [
                # Encabezado
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Celdas generales
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                # Alineación: primera columna a la izquierda, numéricas a la derecha
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                # Fila de totales resaltada
                (
                    "BACKGROUND",
                    (0, last_row_idx_d),
                    (-1, last_row_idx_d),
                    colors.whitesmoke,
                ),
                (
                    "FONTNAME",
                    (0, last_row_idx_d),
                    (-1, last_row_idx_d),
                    "Helvetica-Bold",
                ),
            ]
        )

        # TransaccionDebitos
    df_transa_debitos = tabla_transaccion[
        (tabla_transaccion["cuentaid"] == cuenta_id)
        & (tabla_transaccion["tipooperacion"] == "DEBITO")
    ]
    df_transa_debitos = df_transa_debitos.sort_values(
        "suma_transaccion", ascending=False
    )
    tabla_t_debitos = None
    if not df_transa_debitos.empty:
        cols_numericas_c = ["suma_transaccion", "cant_transacciones"]
        df_transa_debitos[cols_numericas_c] = df_transa_debitos[
            cols_numericas_c
        ].fillna(0)

        data_t_d = [["Moneda", "C_Dest", "Cod_cliente", "Nombre", "Tx", "Monto"]]

        for _, row in df_transa_debitos.iterrows():
            data_t_d.append(
                [
                    row["monedatransaccion"],
                    row["cuentadestino"],
                    row["cod_cliente"],
                    Paragraph(row["nombre_completo"], styles["Cell"]),  # pyright: ignore[reportArgumentType]
                    f"{row['cant_transacciones']:,.2f}",
                    f"{row['suma_transaccion']:,.2f}",
                ]
            )

        tabla_t_debitos = Table(data_t_d, colWidths=[40, 40, 40, 100, 35, 60])
        tabla_t_debitos.setStyle(
            [
                # Encabezado
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Celdas generales
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 6),
                # Alineación: primera columna a la izquierda, numéricas a la derecha
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    else:
        #No transactions found
        tabla_t_debitos = Paragraph("No hay transacciones de débito", styles["Cell"])

    # TransaccionCreditos
    df_transa_creditos = tabla_transaccion[
        (tabla_transaccion["cuentaid"] == cuenta_id)
        & (tabla_transaccion["tipooperacion"] == "CREDITO")
    ]
    df_transa_creditos = df_transa_creditos.sort_values(
        "suma_transaccion", ascending=False
    )
    tabla_t_creditos = None
    if not df_transa_creditos.empty:
        cols_numericas_c = ["suma_transaccion", "cant_transacciones"]
        df_transa_creditos[cols_numericas_c] = df_transa_creditos[
            cols_numericas_c
        ].fillna(0)

        data_t_c = [["Moneda", "C_Dest", "Cod_cliente", "Nombre", "Tx", "Monto"]]

        for _, row in df_transa_creditos.iterrows():
            data_t_c.append(
                [
                    row["monedatransaccion"],
                    row["cuentadestino"],
                    row["cod_cliente"],
                    Paragraph(row["nombre_completo"], styles["Cell"]),  # pyright: ignore[reportArgumentType]
                    f"{row['cant_transacciones']:,.2f}",
                    f"{row['suma_transaccion']:,.2f}",
                ]
            )

        tabla_t_creditos = Table(data_t_c, colWidths=[40, 40, 40, 100, 35, 60])
        tabla_t_creditos.setStyle(
            [
                # Encabezado
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Celdas generales
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 6),
                # Alineación: primera columna a la izquierda, numéricas a la derecha
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    else:
        #No transactions found
        tabla_t_creditos= Paragraph("No hay transacciones de crédito", styles["Cell"])
    # ACHDebitos
    df_ach_debitos = tabla_ach[
        (tabla_ach["cuentaid"] == cuenta_id) & (tabla_ach["tipo_ach"] == "SALIENTE")
    ]
    df_ach_debitos = df_ach_debitos.sort_values("monto_enviado", ascending=False).head(
        10
    )
    tabla_ach_debitos = None
    if not df_ach_debitos.empty:
        data_ach_d = [["Moneda", "B_dest", "C_dest", "Nombre", "Tx", "Monto"]]

        for _, row in df_ach_debitos.iterrows():
            data_ach_d.append(
                [
                    row["moneda"],
                    Paragraph(row["banco_destino"], styles["Cell"]),
                    Paragraph(row["cuenta_destino"], styles["Cell"]),
                    Paragraph(row["nombre_destino"], styles["Cell"]),  # pyright: ignore[reportArgumentType]
                    row["cant"],
                    f"{row['monto_enviado']:,.2f}",
                ]
            )

        tabla_ach_debitos = Table(data_ach_d, colWidths=[40, 50, 50, 100, 35, 60])
        tabla_ach_debitos.setStyle(
            [
                # Encabezado
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Celdas generales
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 6),
                # Alineación: primera columna a la izquierda, numéricas a la derecha
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    else:
        tabla_ach_debitos = Paragraph("No hay transacciones ACH salientes",styles["Cell"])
    # ACHCreditos
    df_ach_creditos = tabla_ach[
        (tabla_ach["cuentaid"] == cuenta_id) & (tabla_ach["tipo_ach"] == "ENTRANTE")
    ]
    df_ach_creditos = df_ach_creditos.sort_values(
        "monto_enviado", ascending=False
    ).head(10)
    tabla_ach_creditos = None
    if not df_ach_creditos.empty:
        data_ach_c = [["Moneda", "B_dest", "C_dest", "Nombre", "Tx", "Monto"]]

        for _, row in df_ach_creditos.iterrows():
            data_ach_c.append(
                [
                    row["moneda"],
                    Paragraph(row["banco_origen"], styles["Cell"]),
                    Paragraph(row["cuenta_origen"], styles["Cell"]),
                    Paragraph(row["nombre_destino"], styles["Cell"]),  # pyright: ignore[reportArgumentType]
                    row["cant"],
                    f"{row['monto_enviado']:,.2f}",
                ]
            )

        tabla_ach_creditos = Table(data_ach_c, colWidths=[40, 50, 50, 100, 35, 60])
        tabla_ach_creditos.setStyle(
            [
                # Encabezado
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                # Celdas generales
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 6),
                # Alineación: primera columna a la izquierda, numéricas a la derecha
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
            ]
        )
    else:
        tabla_ach_creditos= Paragraph("No hay transacciones ACH entrantes",styles["Cell"])

    # ---Contenedor inferior ---
    if tabla_creditos and tabla_debitos:
        bloque_inferior = Table(
            [
                [
                    Paragraph("<b>Causas Créditos</b>", styles["Normal"]),
                    Paragraph("<b>Causas Débitos</b>", styles["Normal"]),
                ],
                [tabla_creditos, tabla_debitos],
            ],
            colWidths=[350, 350],
        )
        bloque_inferior.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elements.append(bloque_inferior)
        elements.append(PageBreak())

    if tabla_agencias_creditos and tabla_agencias_debitos:
        bloque_agencias = Table(
            [
                [
                    Paragraph("<b>Agencias Créditos</b>", styles["Normal"]),
                    Paragraph("<b>Agencias Débitos</b>", styles["Normal"]),
                ],
                [tabla_agencias_creditos, tabla_agencias_debitos],
            ],
            colWidths=[350, 350],
        )
        bloque_agencias.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elements.append(bloque_agencias)
    left_table = tabla_t_creditos if tabla_t_creditos else Spacer(1, 120)
    right_table = tabla_t_debitos if tabla_t_debitos else Spacer(1, 120)

    bloque_transacciones = Table(
        [
            [
                Paragraph("<b>Transacciones Créditos Terceros</b>", styles["Normal"]),
                Paragraph("<b>Transacciones Débitos Terceros</b>", styles["Normal"]),
            ],
            [left_table, right_table],
        ],
        colWidths=[350, 350],
    )
    bloque_transacciones.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(bloque_transacciones)
    elements.append(PageBreak())

    ach_creditos_block = tabla_ach_creditos if tabla_ach_creditos else Spacer(1, 120)
    ach_debitos_block = tabla_ach_debitos if tabla_ach_debitos else Spacer(1, 120)

    bloque_ach = Table(
        [
            [
                Paragraph("<b>ACH Entrantes</b>", styles["Normal"]),
                Paragraph("<b>ACH Salientes</b>", styles["Normal"]),
            ],
            [ach_creditos_block, ach_debitos_block],
        ],
        colWidths=[350, 350],
    )
    bloque_ach.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(bloque_ach)
    elements.append(PageBreak())
