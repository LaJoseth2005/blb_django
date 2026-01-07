from django import forms
from django.contrib.auth.models import User, Group

class RegistroClienteForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit: user.save()
        return user

class RegistroEmpleadosForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    rol = forms.ModelChoiceField(
        queryset=Group.objects.exclude(name='Cliente'), 
        label="Seleccionar Rol del Empleado"
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
            user.groups.add(self.cleaned_data['rol'])
        return user