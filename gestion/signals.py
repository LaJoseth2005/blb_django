from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission, User

@receiver(post_migrate)
def configurar_roles_y_permisos(sender, **kwargs):
    if sender.name != 'gestion':
        return

    bodeguero, _ = Group.objects.get_or_create(name='Bodeguero')
    perms_bodeguero = [
        'add_libro', 'change_libro', 'view_libro',
        'add_autor', 'change_autor', 'view_autor'
    ]
    bodeguero.permissions.set(Permission.objects.filter(codename__in=perms_bodeguero))

    bibliotecario, _ = Group.objects.get_or_create(name='Bibliotecario')
    perms_biblio = [
        'add_prestamo', 'change_prestamo', 'view_prestamo',
        'add_multa', 'change_multa', 'view_multa'
    ]
    bibliotecario.permissions.set(Permission.objects.filter(codename__in=perms_biblio))

    admin_rol, _ = Group.objects.get_or_create(name='Administrador')
    perms_admin = Permission.objects.exclude(
        content_type__app_label__in=['auth', 'admin', 'contenttypes', 'sessions']
    )
    admin_rol.permissions.set(perms_admin)

    cliente, _ = Group.objects.get_or_create(name='Cliente')
    perms_cliente = ['view_libro', 'view_multa']
    cliente.permissions.set(Permission.objects.filter(codename__in=perms_cliente))

@receiver(post_save, sender=User)
def asignar_grupo_cliente(sender, instance, created, **kwargs):
    """Asigna el grupo Cliente a los que se registran solos desde el front"""
    if created and not instance.is_superuser:
        if not instance.groups.exists():
            grupo_cliente = Group.objects.get(name='Cliente')
            instance.groups.add(grupo_cliente)