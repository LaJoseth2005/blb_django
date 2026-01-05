from django.db import models
from django.conf import settings
from django.utils import timezone

from django.contrib.auth.models import User

# Create your models here.

class Autor(models.Model):
    nombre = models.CharField(max_length=50)
    apellido = models.CharField(max_length=50)
    bibliografia = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class Libro(models.Model):
    titulo = models.CharField(max_length=20)
    fecha = models.CharField(max_length=10, blank=True, null=True)
    isbn = models.CharField(max_length=20, blank=True, null=True)
    autor = models.ForeignKey(Autor, related_name="libro", on_delete=models.PROTECT)
    editorial = models.CharField(max_length=255, blank=True, null=True)
    disponible = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.titulo} {self.autor}"


class Prestamo(models.Model):
    libro = models.ForeignKey(Libro, related_name="prestamos", on_delete=models.PROTECT)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="prestamos", on_delete=models.PROTECT)
    fecha_prestamo = models.DateField(default=timezone.now)
    fecha_max = models.DateField(default=timezone.now)
    fecha_devolucion = models.DateField(blank=True, null=True)
    tiene_multa = models.BooleanField(default=False)


    class Meta:
        permissions = (
            ("ver_prestamos", "Puede ver prestamos"),
            ("gestionar_prestamos", "Puede gestionar prestamos"),
        )

    def __str__(self):
        return f"Préstamo de {self.libro} a {self.usuario}"

    @property
    def dias_retraso(self):
        hoy = timezone.now().date()
        fecha_ref = self.fecha_devolucion or hoy
        if fecha_ref > self.fecha_max:
            return (fecha_ref - self.fecha_max).days
        return 0

    @property
    def multa_retraso(self):
        tarifa = 0.50
        return self.dias_retraso * tarifa

    @property
    def multa_perdida(self):
        tarifa = 2.00
        return self.dias_retraso * tarifa

    @property
    def multa_deterioro(self):
        tarifa = 4.00
        return self.dias_retraso * tarifa

    def devolver(self, fecha=None):
        self.fecha_devolucion = fecha or timezone.now().date()
        self.libro.disponible = True
        self.libro.save()
        self.save()

    def generar_multa(self, tipo):
        return Multa.objects.create(
            prestamo=self,
            tipo=tipo
        )

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