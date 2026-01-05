import requests
from datetime import datetime

def obtener_datos_por_isbn(isbn):
    url = f"https://openlibrary.org/isbn/{isbn}.json"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    data = response.json()

    titulo = data.get("title")
    fecha = None
    if "publish_date" in data:
        try:
            fecha = datetime.strptime(data["publish_date"], "%B %d, %Y").date()
        except:
            fecha = None

    editorial = None
    if "publishers" in data:
        editorial = data["publishers"][0] if data["publishers"] else None

    autor_nombre, autor_apellido, autor_bio = None, None, None
    if "authors" in data:
        autor_key = data["authors"][0]["key"]
        autor_url = f"https://openlibrary.org{autor_key}.json"
        autor_resp = requests.get(autor_url)
        if autor_resp.status_code == 200:
            autor_data = autor_resp.json()
            nombre_completo = autor_data.get("name", "")
            partes = nombre_completo.split(" ")
            autor_nombre = partes[0] if partes else None
            autor_apellido = " ".join(partes[1:]) if len(partes) > 1 else None
            autor_bio = autor_data.get("bio")
            if isinstance(autor_bio, dict):
                autor_bio = autor_bio.get("value")

    return {
        "titulo": titulo,
        "fecha": fecha,
        "isbn": isbn,
        "editorial": editorial,
        "autor": {
            "nombre": autor_nombre,
            "apellido": autor_apellido,
            "bibliografia": autor_bio,
        }
    }