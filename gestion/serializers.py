from rest_framework import serializers
from .models import Libro, Autor

class AutorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Autor
        fields = ['nombre', 'apellido', 'bibliografia']

class LibroSerializer(serializers.ModelSerializer):
    autor_detalles = AutorSerializer(source='autor', read_only=True)
    
    class Meta:
        model = Libro
        fields = ['titulo', 'anio', 'isbn', 'autor', 'autor_detalles', 'editorial', 'disponible', 'stock']

    def create(self, validated_data):
        return Libro.objects.create(**validated_data)