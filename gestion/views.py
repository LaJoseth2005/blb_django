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

from .models import Autor, Libro, Prestamo, Multa

def index(request):
    title = settings.TITLE
    return render(request, 'gestion/templates/home.html', {'titulo': title})

def lista_libros(request):
    libros = Libro.objects.all()
    return render(request, 'gestion/templates/libros_view.html', {'libros': libros})

def crear_libros(request):
    autores = Autor.objects.all()
    if request.method == "POST":
        titulo =  request.POST.get('titulo')
        autor_id =  request.POST.get('autor')
        
        if titulo and autor_id:
            autor = get_object_or_404(Autor, id=autor_id)
            Libro.objects.create(titulo=titulo, autor=autor)
            return redirect('lista_libros')
    return render(request, 'gestion/templates/crear_libros.html', {'autores': autores})  

def lista_autores(request):
    autores = Autor.objects.all()
    return render(request, 'gestion/templates/autores.html', {'autores': autores})

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
    return render(request, 'gestion/templates/crear_autores.html', context)

def lista_prestamo(request):
    prestamo = Prestamo.objects.all()
    return render(request, 'gestion/templates/prestamo.html', {'prestamo': prestamo})

@login_required
def crear_prestamo(request):
    if not request.user.has_perm('gestion.gestionar_prestamos'):
        return HttpResponseForbidden()
    libro = Libro.objects.filter(disponible=True)
    usuario = User.objects.all()
    if request.method == 'POST':
        libro_id = request.method.POST.get('libro')
        usuario_id = request.method.POST.get('usuario')
        fecha_prestamo = request.method.POST.get('fecha_prestamo')
        if libro_id and usuario_id and fecha_prestamo:
            libro = get_object_or_404(Libro, id=libro_id)
            usuario = get_object_or_404(User, id=usuario_id)
            prestamo = Prestamo.objects.create(libro = libro,
                                               usuario = usuario,
                                               fecha_prestamo = fecha_prestamo)
            libro.disponible = False
            libro.save()
            return redirect('detalle_prestamo', id=prestamo.id)
    fecha = (timezone.now().date()).isoformat() #YYYY-MM-DD
    return render(request, 'gestion/templates/crear_prestamo.html', {'libros':libro,
                                                                     'usuario': usuario,
                                                                     'fecha': fecha})
def detalle_prestamo(request):
    pass

def lista_multas(request):
    multas = Multa.objects.all()
    return render(request, 'gestion/templates/multas.html', {'multas': multas})

def crear_multas(request):
    pass

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save() #Se guarda el usuario para los permisos
            permiso_user = Permission.objects.get(codename = 'Gestionar_Prestamos') #codename es de donde se tiene el permiso, si no esta lanzaria error
            usuario.user_permissions.add(permiso_user) #aqui se llama al usuario y los permisos que se le asigna
            login(request, usuario)
            return redirect('index') #manda al usuario al index cuando ya se registra
    else:
        form = UserCreationForm()
    return render(request, 'gestion/templates/registration/registro.html', {'form': form})

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