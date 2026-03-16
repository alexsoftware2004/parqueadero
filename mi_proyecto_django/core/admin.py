from django.contrib import admin, messages
from django.utils import timezone

from .models import Cupo, Empleado, Movimiento, Tarifa, Vehiculo

admin.site.site_header = "ParkingHub Admin"
admin.site.site_title = "ParkingHub"
admin.site.index_title = "Panel operativo del sistema de parqueaderos"


@admin.register(Tarifa)
class TarifaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo_vehiculo", "valor_hora", "valor_fraccion", "activo")
    list_filter = ("tipo_vehiculo", "activo")
    search_fields = ("nombre", "tipo_vehiculo")
    list_editable = ("activo",)
    fieldsets = (
        ("Identificacion", {"fields": ("nombre", "tipo_vehiculo", "activo")}),
        ("Cobro", {"fields": ("valor_hora", "valor_fraccion")}),
    )


@admin.register(Cupo)
class CupoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "zona", "estado_operativo", "reservado", "observacion")
    list_filter = ("zona", "disponible", "reservado")
    search_fields = ("codigo", "observacion")
    list_editable = ("reservado",)
    fieldsets = (
        ("Ubicacion", {"fields": ("codigo", "zona")}),
        ("Estado", {"fields": ("disponible", "reservado", "observacion")}),
    )

    @admin.display(description="Estado")
    def estado_operativo(self, obj):
        return "Disponible" if obj.disponible else "Ocupado"


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ("placa", "tipo", "propietario", "telefono", "activo", "fecha_registro")
    list_filter = ("tipo", "activo")
    search_fields = ("placa", "propietario", "telefono")
    list_editable = ("activo",)
    readonly_fields = ("fecha_registro",)
    fieldsets = (
        ("Vehiculo", {"fields": ("placa", "tipo", "activo")}),
        ("Contacto", {"fields": ("propietario", "telefono")}),
        ("Trazabilidad", {"fields": ("fecha_registro",)}),
    )


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = (
        "nombres",
        "apellidos",
        "documento",
        "cargo",
        "turno",
        "activo",
        "usuario",
    )
    list_filter = ("cargo", "turno", "activo")
    search_fields = ("nombres", "apellidos", "documento", "telefono", "correo")
    autocomplete_fields = ("usuario",)
    list_editable = ("activo",)
    fieldsets = (
        ("Identidad", {"fields": ("nombres", "apellidos", "documento")}),
        ("Laboral", {"fields": ("cargo", "turno", "fecha_ingreso", "activo")}),
        ("Contacto", {"fields": ("telefono", "correo")}),
        ("Acceso al sistema", {"fields": ("usuario",)}),
    )


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = (
        "vehiculo",
        "cupo",
        "tarifa",
        "fecha_entrada",
        "fecha_salida",
        "estado",
        "total_pagado",
    )
    list_filter = ("estado", "tarifa__tipo_vehiculo", "cupo__zona")
    search_fields = ("vehiculo__placa", "cupo__codigo", "observacion")
    autocomplete_fields = ("vehiculo", "cupo", "tarifa")
    date_hierarchy = "fecha_entrada"
    actions = ("finalizar_movimientos",)
    readonly_fields = ("fecha_entrada",)
    fieldsets = (
        ("Operacion", {"fields": ("vehiculo", "cupo", "tarifa", "estado")}),
        ("Tiempos", {"fields": ("fecha_entrada", "fecha_salida")}),
        ("Cobro", {"fields": ("total_pagado", "observacion")}),
    )

    @admin.action(description="Finalizar movimientos seleccionados")
    def finalizar_movimientos(self, request, queryset):
        actualizados = 0
        for movimiento in queryset.filter(estado=Movimiento.Estado.ACTIVO):
            movimiento.fecha_salida = timezone.now()
            movimiento.estado = Movimiento.Estado.FINALIZADO
            movimiento.save(update_fields=["fecha_salida", "estado"])
            actualizados += 1
        self.message_user(
            request,
            f"Se finalizaron {actualizados} movimientos activos.",
            level=messages.SUCCESS,
        )
