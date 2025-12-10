from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("", index, name="index"),

    #Gestion Usuarios
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/',auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    #Cambio de contraseña
    path('password/change', auth_views.PasswordChangeView.as_view(), name="password_change"),
    path('passwprd/change/done', auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),

    #Registro
    path('registro/', registro, name="registro"),
    
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