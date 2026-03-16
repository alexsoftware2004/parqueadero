from datetime import date
from django.contrib.auth import get_user_model
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Cupo, Empleado, Movimiento, Tarifa, Vehiculo


class CoreModelsTest(TestCase):
    def setUp(self):
        self.tarifa = Tarifa.objects.create(
            nombre="General",
            tipo_vehiculo=Vehiculo.Tipo.AUTOMOVIL,
            valor_hora=Decimal("5000.00"),
            valor_fraccion=Decimal("2000.00"),
        )
        self.cupo = Cupo.objects.create(codigo="A-01")
        self.vehiculo = Vehiculo.objects.create(placa="abc123", tipo=Vehiculo.Tipo.AUTOMOVIL)

    def test_placa_se_guarda_en_mayusculas(self):
        self.assertEqual(self.vehiculo.placa, "ABC123")

    def test_finalizar_movimiento_actualiza_estado_total_y_cupo(self):
        movimiento = Movimiento.objects.create(
            vehiculo=self.vehiculo,
            cupo=self.cupo,
            tarifa=self.tarifa,
        )

        self.cupo.refresh_from_db()
        self.assertFalse(self.cupo.disponible)

        movimiento.finalizar(Decimal("7000.00"))
        movimiento.refresh_from_db()
        self.cupo.refresh_from_db()

        self.assertEqual(movimiento.estado, Movimiento.Estado.FINALIZADO)
        self.assertEqual(movimiento.total_pagado, Decimal("7000.00"))
        self.assertIsNotNone(movimiento.fecha_salida)
        self.assertTrue(self.cupo.disponible)

    def test_no_permite_dos_movimientos_activos_para_mismo_cupo(self):
        Movimiento.objects.create(vehiculo=self.vehiculo, cupo=self.cupo, tarifa=self.tarifa)
        otro_vehiculo = Vehiculo.objects.create(placa="xyz987", tipo=Vehiculo.Tipo.AUTOMOVIL)
        movimiento = Movimiento(
            vehiculo=otro_vehiculo,
            cupo=self.cupo,
            tarifa=self.tarifa,
        )

        with self.assertRaises(ValidationError):
            movimiento.full_clean()

    def test_empleado_puede_relacionarse_con_usuario(self):
        usuario = get_user_model().objects.create_user(
            username="operador01",
            password="segura123",
        )
        empleado = Empleado.objects.create(
            usuario=usuario,
            nombres="Juan",
            apellidos="Perez",
            documento="12345678",
            cargo=Empleado.Cargo.OPERADOR,
            turno=Empleado.Turno.NOCHE,
            fecha_ingreso=date(2026, 3, 14),
        )

        self.assertEqual(str(empleado), "Juan Perez")
        self.assertEqual(usuario.empleado.documento, "12345678")
