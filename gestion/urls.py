from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path("", views.index, name="index"),

    # Path class view
    path("libros_list/", views.LibroListView.as_view(), name="libro_list"),

    # Gestión Usuarios
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),

    # Cambio de contraseña
    path("password/change", auth_views.PasswordChangeView.as_view(), name="password_change"),
    path("password/change/done", auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),

    # Registro
    path("registro/", views.registro, name="registro"),

    # Libros
    path("libros/", views.lista_libros, name="lista_libros"),
    path("libros/nuevo/", views.crear_libros, name="crear_libros"),
    path("importar-libro/", views.importar_libro, name="importar_libro"),
    path("libros/<int:pk>/editar_libros", views.LibroUpdateView.as_view(), name="editar_libros"),

    # Autores
    path("autores/", views.lista_autores, name="lista_autores"),
    path("autores/nuevo/", views.crear_autores, name="crear_autores"),
    path("autores/<int:id>/editar/", views.crear_autores, name="editar_autor"),

    # Prestamos
    path("prestamos/", views.lista_prestamos, name="lista_prestamos"),
    path("prestamos/nuevo/", views.crear_prestamo, name="crear_prestamo"),
    path("prestamos/<int:id>", views.detalle_prestamo, name="detalle_prestamo"),
    path("prestamos/<int:id>/devolver/", views.devolver_prestamo, name="devolver_prestamo"),
    path("prestamos/<int:pk>/editar_prestamo", views.PrestamoUpdateView.as_view(), name="editar_prestamo"),

    # Multas
    path("multas/", views.lista_multas, name="lista_multas"),
    path("multas/nuevo/", views.crear_multas, name="crear_multas_sin_id"),
    path("multas/nuevo/<int:prestamo_id>", views.crear_multas, name="crear_multas"),
    path("multas/<int:pk>/editar_multas", views.MultaUpdateView.as_view(), name="editar_multas"),
]