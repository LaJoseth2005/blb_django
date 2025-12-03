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
    pass

def crear_libros(request):
    pass

def lista_autores(request):
    autores = Autor.objects.all()
    return render(request, 'gestion/templates/autores.html', {'autores': autores})
    pass

def crear_autores(request):
    pass

def lista_prestamo(request):
    pass

def crear_prestamo(request):
    pass

def detalle_prestamo(request):
    pass

def lista_multas(request):
    pass

def crear_multas(request):
    pass