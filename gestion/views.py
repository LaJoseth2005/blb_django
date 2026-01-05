from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Permission
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseForbidden
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.utils import timezone
from django.conf import settings
from .openlibrary import obtener_datos_por_isbn

from .models import Autor, Libro, Prestamo, Multa

def index(request):
    title = settings.TITLE
    return render(request, 'home.html', {'titulo': title})

def lista_libros(request):
    libros = Libro.objects.all()
    return render(request, 'libros_view.html', {'libros': libros})

def crear_libros(request):
    autores = Autor.objects.all()
    if request.method == "POST":
        titulo =  request.POST.get('titulo')
        autor_id =  request.POST.get('autor')
        
        if titulo and autor_id:
            autor = get_object_or_404(Autor, id=autor_id)
            Libro.objects.create(titulo=titulo, autor=autor)
            return redirect('lista_libros')
    return render(request, 'crear_libros.html', {'autores': autores})  

def lista_autores(request):
    autores = Autor.objects.all()
    return render(request, 'autores.html', {'autores': autores})

@login_required
def crear_autores(request, id=None):
    if id == None:
        autor = None
        modo = 'Crear'
    else:
        autor = get_object_or_404(Autor, id=id)
        modo = 'editar'

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        bibliografia = request.POST.get('bibliografia')

        if autor == None:
            Autor.objects.create(nombre=nombre, apellido=apellido, bibliografia=bibliografia)
        else:
            autor.apellido = apellido
            autor.nombre = nombre
            autor.bibliografia = bibliografia
            autor.save()
        return redirect('lista_autores')
    context = {'autor': autor,
               'titulo': 'Editar Autor' if modo == 'editar' else 'Crear Autor',
               'texto_boton': 'Guardar cambios' if modo == 'editar' else 'Crear'}
    return render(request, 'crear_autores.html', context)

@login_required
def lista_prestamo(request):
    prestamos = Prestamo.objects.filter(
        fecha_devolucion__isnull=True,
        tiene_multa=False
    )
    return render(request, "prestamo.html", {"prestamos": prestamos})

@login_required
def devolver_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, id=id)
    prestamo.libro.disponible = True
    prestamo.libro.save()
    prestamo.fecha_devolucion = timezone.now().date()
    prestamo.save()
    return redirect("lista_prestamos")

def importar_libro(request):
    autores = Autor.objects.all()
    mensaje = None

    if request.method == "POST":
        isbn_input = request.POST.get("isbn")
        if isbn_input:
            datos = obtener_datos_por_isbn(isbn_input) 
            
            if datos:
                isbn_api = datos["isbn"]
                if Libro.objects.filter(isbn=isbn_api).exists():
                    mensaje = f"El libro '{datos['titulo']}' (ISBN: {isbn_api}) ya está registrado."
                else:
                    autor_info = datos["autor"]
                    autor, _ = Autor.objects.get_or_create(
                        nombre=autor_info["nombre"],
                        apellido=autor_info["apellido"],
                        defaults={"bibliografia": autor_info.get("bibliografia", "")}
                    )
                    Libro.objects.create(
                        titulo=datos["titulo"],
                        fecha=datos["fecha"],
                        isbn=isbn_api,
                        editorial=datos["editorial"],
                        autor=autor,
                        disponible=True
                    )
                    return redirect("lista_libros")
            else:
                mensaje = "No se pudo obtener datos del ISBN o no existe en OpenLibrary."

    return render(request, "crear_libros.html", {
        "autores": autores, 
        "mensaje": mensaje
    })

@login_required
def crear_prestamo(request):
    if not request.user.has_perm('gestion.gestionar_prestamos'):
        return HttpResponseForbidden()
    
    libros = Libro.objects.filter(disponible=True)
    usuarios = User.objects.all()
    
    if request.method == 'POST':
        libro_id = request.POST.get('libro')
        usuario_id = request.POST.get('usuario')
        fecha_prestamo = request.POST.get('fecha_prestamo')
        fecha_max = timezone.now().date() + timezone.timedelta(days=7)

        if libro_id and usuario_id and fecha_prestamo:
            libro = get_object_or_404(Libro, id=libro_id)
            usuario = get_object_or_404(User, id=usuario_id)
            prestamo = Prestamo.objects.create(
                libro=libro,
                usuario=usuario,
                fecha_prestamo=fecha_prestamo,
                fecha_max=fecha_max
            )
            libro.disponible = False
            libro.save()
            return redirect('detalle_prestamo', id=prestamo.id)
    
    fecha = timezone.now().date().isoformat()  # YYYY-MM-DD
    return render(request, 'crear_prestamo.html', {
        'libros': libros,
        'usuario': usuarios,
        'fecha': fecha
    })

def detalle_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, id=id)
    return render(request, 'detalle_prestamo.html', {'prestamo': prestamo})

def lista_multas(request):
    multas = Multa.objects.all()
    return render(request, 'multas.html', {'multas': multas})

@login_required
def crear_multas(request, prestamo_id=None):
    if prestamo_id is None:
        prestamos = Prestamo.objects.filter(fecha_devolucion__isnull=True, tiene_multa=False)
        fecha = timezone.now().date()
        return render(request, "crear_multas.html", {
            "prestamos": prestamos,
            "prestamo_seleccionado": None,
            "fecha": fecha
        })

    prestamo = get_object_or_404(Prestamo, id=prestamo_id)
    hoy = timezone.now().date()

    if request.method == "POST":
        tipo = request.POST.get("tipo")
        monto = request.POST.get("monto")
        fecha = request.POST.get("fecha")
        pagada = True if request.POST.get("pagada") else False

        Multa.objects.create(
            prestamo=prestamo,
            tipo=tipo,
            monto=monto,
            fecha=fecha,
            pagada=pagada
        )

        # marcar el préstamo como multado para que no aparezca en pendientes
        prestamo.tiene_multa = True
        prestamo.save()

        return redirect("lista_multas")

    return render(request, "crear_multas.html", {
        "prestamos": Prestamo.objects.all(),
        "prestamo_seleccionado": prestamo,
        "fecha": hoy
    })

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
    
            try:
                permiso = Permission.objects.get(codename='gestionar_prestamos')
                usuario.user_permissions.add(permiso)
            except Permission.DoesNotExist:
                print("⚠️ ADVERTENCIA: El permiso 'gestionar_prestamos' no existe en la BD. Recuerda hacer migrate.")

            login(request, usuario)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registro.html', {'form': form})

class LibroListView(LoginRequiredMixin, ListView):
    model = Libro
    template = 'gestion/templates/libro_list.html'
    context_object_name = 'libros'
    paginate_by = 3

class LibroDetalleView(LoginRequiredMixin, DetailView):
    model = Libro
    template = 'gestion/templates/detalle_libros.html'
    context_object_name = 'libro'

class LibroCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Libro
    fields = ['titulo', 'autor', 'disponible']
    template_name =  'gestion/templates/crear_libros.html'
    success_url = reverse_lazy('libro_list')
    pemission_required = 'gestion.add_libro'

class LibroUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Libro
    fields = ['titulo', 'autor']
    template_name =  'gestion/templates/editar_libros.html'
    success_url = reverse_lazy('libro_list')
    pemission_required = 'gestion.change_libro'

class LibroUpdateView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Libro
    template_name = 'gestion/templates/delete_libros.html'
    success_url = reverse_lazy('libro_list')
    pemission_required = 'gestion.delete_libro'