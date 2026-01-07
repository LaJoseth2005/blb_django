from django.db import models
from django.conf import settings
from django.utils import timezone

from django.contrib.auth.models import User

# Create your models here.

class Autor(models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50, blank=True, null=True)
    bibliografia = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Libro(models.Model):
    titulo = models.CharField(max_length=20)
    anio = models.IntegerField(blank=True, null=True)
    isbn = models.CharField(max_length=20, blank=True, null=True)
    autor = models.ForeignKey(Autor, related_name="libro", on_delete=models.PROTECT)
    editorial = models.CharField(max_length=255, blank=True, null=True)
    disponible = models.BooleanField(default=True)
    stock = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.titulo} {self.autor}"

    def disminuir_stock(self, cantidad=1):
        """Disminuye el stock al hacer un préstamo/pedido."""
        if self.stock and self.stock >= cantidad:
            self.stock -= cantidad
            if self.stock == 0:
                self.disponible = False
            self.save()

    def aumentar_stock(self, cantidad=1):
        """Aumenta el stock al devolver un libro."""
        if self.stock is None:
            self.stock = 0
        self.stock += cantidad
        if self.stock > 0:
            self.disponible = True
        self.save()

    def marcar_danado_o_perdido(self, cantidad=1):
        """Reduce stock permanentemente si el libro se daña o se pierde."""
        if self.stock and self.stock >= cantidad:
            self.stock -= cantidad
            if self.stock == 0:
                self.disponible = False
            self.save()


class Prestamo(models.Model):
    estados = [
        ('solicitado', 'Solicitado'),
        ('aprobado', 'Aprobado'),
        ('devuelto', 'Devuelto'),
    ]

    libro = models.ForeignKey(Libro, related_name="prestamos", on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="prestamos", on_delete=models.PROTECT)
    fecha_prestamo = models.DateField(default=timezone.now)
    fecha_max = models.DateField(default=timezone.now)
    fecha_devolucion = models.DateField(blank=True, null=True)
    tiene_multa = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, choices=estados, default='solicitado')

    class Meta:
        permissions = (
            ("ver_prestamos", "Puede ver prestamos"),
            ("gestionar_prestamos", "Puede gestionar prestamos"),
        )

    def __str__(self):
        return f"Préstamo de {self.libro} a {self.usuario} ({self.get_estado_display()})"

class Multa(models.Model):
    prestamo = models.ForeignKey(Prestamo, related_name="multas", on_delete=models.PROTECT)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    tipo = models.CharField(
        max_length=10,
        choices=(
            ('r', 'retraso'),
            ('p', 'perdida'),
            ('d', 'deterioro')
        )
    )
    monto = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    pagada = models.BooleanField(default=False)
    fecha = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Multa {self.tipo} - {self.monto} - {self.prestamo}"

    def save(self, *args, **kwargs):
        if self.tipo == 'r' and self.monto == 0:
            self.monto = self.prestamo.multa_retraso
        elif self.tipo == 'p' and self.monto == 0:
            self.monto = self.prestamo.multa_perdida
        elif self.tipo == 'd' and self.monto == 0:
            self.monto = self.prestamo.multa_deterioro
        super().save(*args, **kwargs)