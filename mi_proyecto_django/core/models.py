from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Tarifa(models.Model):
    nombre = models.CharField(max_length=80)
    tipo_vehiculo = models.CharField(max_length=30)
    valor_hora = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    valor_fraccion = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Cobro base para periodos menores a una hora.",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["tipo_vehiculo", "nombre"]
        verbose_name = "Tarifa"
        verbose_name_plural = "Tarifas"

    def __str__(self):
        return f"{self.nombre} - {self.tipo_vehiculo}"


class Cupo(models.Model):
    class Zona(models.TextChoices):
        SOTANO = "sotano", "Sotano"
        PRIMER_PISO = "primer_piso", "Primer piso"
        SEGUNDO_PISO = "segundo_piso", "Segundo piso"
        EXTERIOR = "exterior", "Exterior"

    codigo = models.CharField(max_length=20, unique=True)
    zona = models.CharField(max_length=20, choices=Zona.choices, default=Zona.PRIMER_PISO)
    disponible = models.BooleanField(default=True)
    reservado = models.BooleanField(default=False)
    observacion = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["codigo"]
        verbose_name = "Cupo"
        verbose_name_plural = "Cupos"

    def __str__(self):
        return self.codigo


class Vehiculo(models.Model):
    class Tipo(models.TextChoices):
        AUTOMOVIL = "automovil", "Automovil"
        MOTO = "moto", "Moto"
        CAMIONETA = "camioneta", "Camioneta"
        BICICLETA = "bicicleta", "Bicicleta"

    placa = models.CharField(max_length=10, unique=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    propietario = models.CharField(max_length=120, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["placa"]
        verbose_name = "Vehiculo"
        verbose_name_plural = "Vehiculos"

    def __str__(self):
        return f"{self.placa} ({self.get_tipo_display()})"

    def save(self, *args, **kwargs):
        self.placa = self.placa.upper().strip()
        super().save(*args, **kwargs)


class Empleado(models.Model):
    class Cargo(models.TextChoices):
        OPERADOR = "operador", "Operador"
        CAJERO = "cajero", "Cajero"
        SUPERVISOR = "supervisor", "Supervisor"
        ADMINISTRADOR = "administrador", "Administrador"

    class Turno(models.TextChoices):
        MANANA = "manana", "Manana"
        TARDE = "tarde", "Tarde"
        NOCHE = "noche", "Noche"

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="empleado",
        null=True,
        blank=True,
    )
    nombres = models.CharField(max_length=80)
    apellidos = models.CharField(max_length=80)
    documento = models.CharField(max_length=20, unique=True)
    telefono = models.CharField(max_length=30, blank=True)
    correo = models.EmailField(blank=True)
    cargo = models.CharField(max_length=20, choices=Cargo.choices)
    turno = models.CharField(max_length=20, choices=Turno.choices)
    fecha_ingreso = models.DateField()
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ["apellidos", "nombres"]
        verbose_name = "Empleado"
        verbose_name_plural = "Empleados"

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"


class Movimiento(models.Model):
    class Estado(models.TextChoices):
        ACTIVO = "activo", "Activo"
        FINALIZADO = "finalizado", "Finalizado"

    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.PROTECT, related_name="movimientos")
    cupo = models.ForeignKey(Cupo, on_delete=models.PROTECT, related_name="movimientos")
    tarifa = models.ForeignKey(Tarifa, on_delete=models.PROTECT, related_name="movimientos")
    fecha_entrada = models.DateTimeField(default=timezone.now)
    fecha_salida = models.DateTimeField(blank=True, null=True)
    total_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVO)
    observacion = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ["-fecha_entrada"]
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"

    def __str__(self):
        return f"{self.vehiculo.placa} en {self.cupo.codigo}"

    def clean(self):
        if self.estado == self.Estado.ACTIVO and self.fecha_salida:
            raise ValidationError("Un movimiento activo no puede tener fecha de salida.")
        if self.estado == self.Estado.FINALIZADO and not self.fecha_salida:
            raise ValidationError("Un movimiento finalizado requiere fecha de salida.")

        conflicto_cupo = Movimiento.objects.filter(cupo=self.cupo, estado=self.Estado.ACTIVO)
        conflicto_vehiculo = Movimiento.objects.filter(
            vehiculo=self.vehiculo,
            estado=self.Estado.ACTIVO,
        )
        if self.pk:
            conflicto_cupo = conflicto_cupo.exclude(pk=self.pk)
            conflicto_vehiculo = conflicto_vehiculo.exclude(pk=self.pk)

        if self.estado == self.Estado.ACTIVO and conflicto_cupo.exists():
            raise ValidationError("El cupo ya tiene un movimiento activo.")
        if self.estado == self.Estado.ACTIVO and conflicto_vehiculo.exists():
            raise ValidationError("El vehiculo ya tiene un movimiento activo.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.cupo.disponible = self.estado != self.Estado.ACTIVO
        self.cupo.save(update_fields=["disponible"])

    def finalizar(self, total_pagado):
        self.fecha_salida = timezone.now()
        self.total_pagado = total_pagado
        self.estado = self.Estado.FINALIZADO
        self.save(update_fields=["fecha_salida", "total_pagado", "estado"])
