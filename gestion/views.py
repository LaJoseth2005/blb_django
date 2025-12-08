from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

from .models import Autor, Libro, Prestamo, Multa

def index(request):
    title = settings.TITLE
    return render(request, 'gestion/templates/home.html', {'titulo': title})

def lista_libros(request):
    libros = Libro.objects.all()
    return render(request, 'gestion/templates/libros.html', {'libros': libros})

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

def crear_prestamo(request):
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