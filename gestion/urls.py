from django.urls import path
from .views import *

urlpatterns = [
    path("", index, name="index"),
    
    #libros
    path('libros/', lista_libros, name="lista_libros"),
    path('libros/nuevo/', crear_libros, name="crear_libros"),
    
    #autores
    path('autores/', lista_autores, name="lista_autores"),
    path('autores/nuevo/', crear_autores, name="crear_autores"),
    path('autores/<int:id>/editar/', crear_autores, name="editar_autor"),


    #prestamos
    path('prestamos/', lista_prestamo, name="lista_prestamos"),
    path('prestamos/nuevo/', crear_prestamo, name="crear_prestamo"),
    path('prestamos/<int:id>', detalle_prestamo, name="detalle_prestamo"),
    
    #multas
    path('multas/', lista_multas, name="lista_multas"),
    path('multas/nuevo/<int:prestamo_id>', crear_multas, name="crear_multas"),
    
    #Path es la url de paths secundarios 
]