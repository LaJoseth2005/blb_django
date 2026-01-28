from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import HttpResponseForbidden
from django.contrib.auth import login, get_user_model
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.urls import reverse_lazy
from django.utils import timezone
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import LibroSerializer

from .models import Autor, Libro, Prestamo, Multa
from .forms import RegistroClienteForm, RegistroEmpleadosForm 
from .openlibrary import obtener_datos_por_isbn


def index(request):
    title = settings.TITLE
    return render(request, 'home.html', {'titulo': title})


class LibroViewSet(viewsets.ModelViewSet):
    queryset = Libro.objects.all()
    serializer_class = LibroSerializer
    lookup_field = 'isbn' # Buscaremos por ISBN en lugar de ID

    def retrieve(self, request, *args, **kwargs):
        isbn = kwargs.get('isbn')
        try:
            libro = Libro.objects.get(isbn=isbn)
            serializer = self.get_serializer(libro)
            return Response(serializer.data)
        except Libro.DoesNotExist:
            return Response({"error": "No encontrado"}, status=status.HTTP_404_NOT_FOUND)

def lista_libros(request):
    libros = Libro.objects.all()
    return render(request, 'libros_view.html', {'libros': libros})

def lista_autores(request):
    autores = Autor.objects.all()
    return render(request, 'autores.html', {'autores': autores})

def registro_cliente(request):
    """Registro para Clientes - CORREGIDO: Ruta a gestion/"""
    if request.method == 'POST':
        form = RegistroClienteForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)
            return redirect('index')
    else:
        form = RegistroClienteForm()
    return render(request, 'registro.html', {'form': form})

@user_passes_test(lambda u: u.is_superuser)
def crear_empleado(request):
    """Registro solo para Superusuario - CORREGIDO: Ruta a gestion/"""
    if request.method == 'POST':
        form = RegistroEmpleadosForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = RegistroEmpleadosForm()
    return render(request, 'crear_empleado.html', {'form': form})

@login_required
def crear_libros(request):
    if not request.user.has_perm('gestion.add_libro'):
        return HttpResponseForbidden("No tienes permiso para agregar libros.")
        
    autores = Autor.objects.all()
    if request.method == "POST":
        titulo = request.POST.get('titulo')
        autor_id = request.POST.get('autor')
        anio = request.POST.get('anio')
        stock_manual = request.POST.get("stock_manual")

        if titulo and autor_id and stock_manual:
            autor = get_object_or_404(Autor, id=autor_id)
            Libro.objects.create(
                titulo=titulo,
                autor=autor,
                anio=anio if anio else None,
                stock=int(stock_manual),
                disponible=True
            )
            return redirect('lista_libros')

    return render(request, 'crear_libros.html', {'autores': autores})

@login_required
def crear_autores(request, id=None):
    if not request.user.has_perm('gestion.add_autor'):
        return HttpResponseForbidden("No tienes permiso para gestionar autores.")

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
        
    context = {
        'autor': autor,
        'titulo': 'Editar Autor' if modo == 'editar' else 'Crear Autor',
        'texto_boton': 'Guardar cambios' if modo == 'editar' else 'Crear'
    }
    return render(request, 'crear_autores.html', context)

@login_required
def importar_libro(request):
    if not request.user.has_perm('gestion.add_libro'):
        return HttpResponseForbidden()

    autores = Autor.objects.all()
    mensaje = None

    if request.method == "POST":
        isbn_input = request.POST.get("isbn")
        stock_openlibrary = request.POST.get("stock_openlibrary")

        if isbn_input and stock_openlibrary:
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
                        anio=datos["anio"],
                        isbn=isbn_api,
                        editorial=datos["editorial"],
                        autor=autor,
                        disponible=True,
                        stock=int(stock_openlibrary)
                    )
                    return redirect("lista_libros")
            else:
                mensaje = "No se pudo obtener datos del ISBN."

    return render(request, "crear_libros.html", {"autores": autores, "mensaje": mensaje})



@login_required
def solicitar_prestamo_cliente(request, libro_id):
    """El cliente solicita. El stock NO baja todavía."""
    libro = get_object_or_404(Libro, id=libro_id)
    if libro.stock > 0:
        Prestamo.objects.create(
            libro=libro,
            usuario=request.user,
            fecha_prestamo=timezone.now().date(),
            fecha_max=timezone.now().date() + timezone.timedelta(days=7),
            estado='solicitado'
        )
    return redirect('lista_prestamos')

@login_required
def aprobar_prestamo(request, id):
    """Solo el Bibliotecario aprueba. Aquí es donde BAJA EL STOCK."""
    if not request.user.has_perm('gestion.change_prestamo'):
        return HttpResponseForbidden()
    
    prestamo = get_object_or_404(Prestamo, id=id)
    if prestamo.estado == 'solicitado':
        prestamo.estado = 'aprobado'
        prestamo.libro.disminuir_stock() 
        prestamo.save()
    return redirect('lista_prestamos')

@login_required
def lista_prestamos(request):
    """Vista compartida: Oculta los que tienen multa para evitar duplicidad visual"""
    if request.user.has_perm('gestion.change_prestamo'):
        prestamos = Prestamo.objects.filter(fecha_devolucion__isnull=True, tiene_multa=False)
    else:
        prestamos = Prestamo.objects.filter(usuario=request.user, fecha_devolucion__isnull=True, tiene_multa=False)
    return render(request, "prestamo.html", {"prestamos": prestamos})

@login_required
def crear_prestamo(request):
    """Crea préstamo directo por Bibliotecario (Baja stock inmediatamente)"""
    if not request.user.has_perm('gestion.add_prestamo'):
        return HttpResponseForbidden()
    
    libros = Libro.objects.filter(stock__gt=0)
    usuarios = User.objects.all()
    
    if request.method == 'POST':
        libro_id = request.POST.get('libro')
        usuario_id = request.POST.get('usuario')
        fecha_prestamo = request.POST.get('fecha_prestamo')
        fecha_max = timezone.now().date() + timezone.timedelta(days=7)

        if libro_id and usuario_id and fecha_prestamo:
            libro = get_object_or_404(Libro, id=libro_id)
            usuario = get_object_or_404(User, id=usuario_id)

            if Multa.objects.filter(usuario=usuario, pagada=False).exists():
                return render(request, 'crear_prestamo.html', {
                    'libros': libros, 'usuarios': usuarios,
                    'fecha': timezone.now().date().isoformat(),
                    'error': "Este usuario tiene multas pendientes."
                })

            prestamo = Prestamo.objects.create(
                libro=libro, 
                usuario=usuario, 
                fecha_prestamo=fecha_prestamo, 
                fecha_max=fecha_max, 
                estado='aprobado'
            )
            libro.disminuir_stock()
            return redirect('lista_prestamos')
    
    return render(request, 'crear_prestamo.html', {
        'libros': libros, 'usuarios': usuarios, 'fecha': timezone.now().date().isoformat()
    })

@login_required
def devolver_prestamo(request, id):
    if not request.user.has_perm('gestion.change_prestamo'):
        return HttpResponseForbidden()
    prestamo = get_object_or_404(Prestamo, id=id)
    prestamo.libro.aumentar_stock()
    prestamo.fecha_devolucion = timezone.now().date()
    prestamo.estado = 'devuelto'
    prestamo.save()
    return redirect("lista_prestamos")

def detalle_prestamo(request, id):
    prestamo = get_object_or_404(Prestamo, id=id)
    return render(request, 'detalle_prestamo.html', {'prestamo': prestamo})


@login_required
def lista_multas(request):
    if request.user.has_perm('gestion.view_multa'):
        multas = Multa.objects.all()
    else:
        multas = Multa.objects.filter(usuario=request.user)
    return render(request, 'multas.html', {'multas': multas})

@login_required
def pagar_multa(request, id):
    multa = get_object_or_404(Multa, id=id, usuario=request.user)
    multa.pagada = True
    multa.save()
    return redirect('lista_multas')

@login_required
def crear_multas(request, prestamo_id=None):
    if not request.user.has_perm('gestion.add_multa'):
        return HttpResponseForbidden()

    if prestamo_id is None:
        prestamos = Prestamo.objects.filter(fecha_devolucion__isnull=True, tiene_multa=False)
        return render(request, "crear_multas.html", {"prestamos": prestamos, "fecha": timezone.now().date()})

    prestamo = get_object_or_404(Prestamo, id=prestamo_id)

    if request.method == "POST":
        Multa.objects.create(
            prestamo=prestamo,
            usuario=prestamo.usuario,
            tipo=request.POST.get("tipo"),
            monto=request.POST.get("monto"),
            fecha=request.POST.get("fecha"),
            pagada=True if request.POST.get("pagada") else False
        )
        prestamo.tiene_multa = True
        prestamo.save()
        return redirect("lista_multas")

    return render(request, "crear_multas.html", {
        "prestamos": Prestamo.objects.all(),
        "prestamo_seleccionado": prestamo,
        "fecha": timezone.now().date()
    })


def render_to_pdf(template_src, context_dict):
    """Función de utilidad para convertir HTML en PDF"""
    template = get_template(template_src)
    html  = template.render(context_dict)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="reporte_biblioteca.pdf"'
    
    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
       return HttpResponse('Error técnico al generar el reporte PDF', status=500)
    return response

def es_admin_o_staff(user):
    """Retorna True si el usuario es staff o pertenece al grupo 'Administrador'"""
    return user.is_authenticated and (user.is_staff or user.groups.filter(name='Administrador').exists())

@login_required
@user_passes_test(es_admin_o_staff)
def reporte_prestamos_pdf(request):
    items = Prestamo.objects.filter(fecha_devolucion__isnull=True).select_related('libro', 'usuario')
    data = {
        'titulo_reporte': 'INFORME DE LIBROS PRESTADOS (CIRCULACIÓN)',
        'items': items,
        'fecha': timezone.now().date(),
        'tipo': 'prestamos'
    }
    return render_to_pdf('pdf_base.html', data)

@login_required
@user_passes_test(es_admin_o_staff)
def reporte_multas_pdf(request):
    items = Multa.objects.all().select_related('usuario', 'prestamo')
    data = {
        'titulo_reporte': 'REPORTE GENERAL DE MULTAS EXISTENTES',
        'items': items,
        'fecha': timezone.now().date(),
        'tipo': 'multas_general'
    }
    return render_to_pdf('pdf_base.html', data)

@login_required
@user_passes_test(es_admin_o_staff)
def reporte_usuarios_detalle_pdf(request):
    usuarios = User.objects.filter(multa__isnull=False).distinct().prefetch_related('multa_set')
    data = {
        'titulo_reporte': 'DETALLE DE MULTAS POR CADA USUARIO',
        'usuarios_list': usuarios,
        'fecha': timezone.now().date(),
        'tipo': 'usuarios_detalle'
    }
    return render_to_pdf('pdf_base.html', data)


class LibroListView(LoginRequiredMixin, ListView):
    model = Libro
    template_name = 'gestion/templates/libro_list.html'
    context_object_name = 'libros'
    paginate_by = 3

class LibroDetalleView(LoginRequiredMixin, DetailView):
    model = Libro
    template_name = 'gestion/templates/detalle_libros.html'
    context_object_name = 'libro'

class LibroCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Libro
    fields = ['titulo', 'autor', 'disponible']
    template_name = 'gestion/templates/crear_libros.html'
    success_url = reverse_lazy('libro_list')
    permission_required = 'gestion.add_libro'

class LibroUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Libro
    fields = ['titulo', 'anio', 'isbn', 'autor', 'editorial', 'disponible', 'stock']
    template_name = 'editar_libros.html'
    success_url = reverse_lazy('lista_libros')
    permission_required = 'gestion.change_libro'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['autores'] = Autor.objects.all()
        return context

class PrestamoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Prestamo
    fields = ['libro', 'usuario', 'fecha_prestamo', 'fecha_max', 'fecha_devolucion', 'tiene_multa', 'estado']
    template_name = 'editar_prestamo.html'
    success_url = reverse_lazy('lista_prestamos')
    permission_required = 'gestion.change_prestamo'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['libros'] = Libro.objects.all()
        context['usuarios'] = get_user_model().objects.all()
        context['prestamo'] = self.object
        return context

class MultaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Multa
    fields = ['tipo', 'monto', 'pagada', 'fecha'] 
    template_name = 'editar_multas.html'
    success_url = reverse_lazy('lista_multas')
    permission_required = 'gestion.change_multa'