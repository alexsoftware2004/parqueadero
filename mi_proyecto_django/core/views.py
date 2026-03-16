from django.db.models import Count
from django.shortcuts import render

from .models import Cupo, Empleado, Movimiento, Tarifa, Vehiculo


def inicio(request):
    total_cupos = Cupo.objects.count()
    cupos_disponibles = Cupo.objects.filter(disponible=True).count()
    movimientos_activos = Movimiento.objects.filter(estado=Movimiento.Estado.ACTIVO)
    vehiculos_registrados = Vehiculo.objects.filter(activo=True).count()
    tarifas_activas = Tarifa.objects.filter(activo=True).count()
    empleados_activos = Empleado.objects.filter(activo=True).count()
    ocupacion_porcentaje = 0
    if total_cupos:
        ocupacion_porcentaje = round(((total_cupos - cupos_disponibles) / total_cupos) * 100)

    estadisticas = [
        {"valor": total_cupos or "0", "etiqueta": "Cupos totales"},
        {"valor": movimientos_activos.count(), "etiqueta": "Vehiculos activos"},
        {"valor": cupos_disponibles, "etiqueta": "Espacios disponibles"},
        {"valor": f"{ocupacion_porcentaje}%", "etiqueta": "Ocupacion actual"},
    ]

    zonas = []
    for zona, etiqueta in Cupo.Zona.choices:
        total_zona = Cupo.objects.filter(zona=zona).count()
        disponibles_zona = Cupo.objects.filter(zona=zona, disponible=True).count()
        ocupados_zona = total_zona - disponibles_zona
        porcentaje = 0
        if total_zona:
            porcentaje = round((ocupados_zona / total_zona) * 100)
        zonas.append(
            {
                "nombre": etiqueta,
                "total": total_zona,
                "disponibles": disponibles_zona,
                "ocupados": ocupados_zona,
                "porcentaje": porcentaje,
            }
        )

    distribucion_vehiculos = list(
        Vehiculo.objects.filter(activo=True)
        .values("tipo")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    for item in distribucion_vehiculos:
        item["label"] = dict(Vehiculo.Tipo.choices).get(item["tipo"], item["tipo"])

    recientes = list(Movimiento.objects.select_related("vehiculo", "cupo", "tarifa")[:5])

    context = {
        "estadisticas": estadisticas,
        "resumen": {
            "vehiculos_registrados": vehiculos_registrados,
            "tarifas_activas": tarifas_activas,
            "movimientos_abiertos": movimientos_activos.count(),
            "empleados_activos": empleados_activos,
        },
        "modulos": [
            {
                "titulo": "Ingreso rapido",
                "descripcion": "Crea movimientos, asigna cupos y consulta placas sin navegar por menus innecesarios.",
                "ruta": "/admin/core/movimiento/add/",
                "cta": "Registrar entrada",
            },
            {
                "titulo": "Control de cupos",
                "descripcion": "Detecta zonas saturadas, reservas y disponibilidad operativa en una sola vista.",
                "ruta": "/admin/core/cupo/",
                "cta": "Ver cupos",
            },
            {
                "titulo": "Tarifas y recaudo",
                "descripcion": "Mantiene reglas de cobro activas por tipo de vehiculo y mejora el cierre de turno.",
                "ruta": "/admin/core/tarifa/",
                "cta": "Gestionar tarifas",
            },
            {
                "titulo": "Equipo operativo",
                "descripcion": "Organiza empleados, turnos y responsables del parqueadero desde un modulo dedicado.",
                "ruta": "/admin/core/empleado/",
                "cta": "Administrar empleados",
            },
        ],
        "pasos_iniciales": [
            {
                "titulo": "1. Crear tarifas",
                "descripcion": "Define el valor por hora y fraccion para cada tipo de vehiculo.",
                "ruta": "/admin/core/tarifa/add/",
            },
            {
                "titulo": "2. Registrar cupos",
                "descripcion": "Carga cupos por zonas para activar el mapa de ocupacion y disponibilidad.",
                "ruta": "/admin/core/cupo/add/",
            },
            {
                "titulo": "3. Vincular empleados",
                "descripcion": "Asigna usuarios y turnos para que el equipo opere con roles claros.",
                "ruta": "/admin/core/empleado/add/",
            },
            {
                "titulo": "4. Crear el primer ingreso",
                "descripcion": "Registra un movimiento para activar el flujo real del parqueadero.",
                "ruta": "/admin/core/movimiento/add/",
            },
        ],
        "sistema_vacio": not any(
            [
                total_cupos,
                movimientos_activos.count(),
                vehiculos_registrados,
                empleados_activos,
                tarifas_activas,
            ]
        ),
        "zonas": zonas,
        "distribucion_vehiculos": distribucion_vehiculos,
        "recientes": recientes,
    }
    return render(request, "core/inicio.html", context)
