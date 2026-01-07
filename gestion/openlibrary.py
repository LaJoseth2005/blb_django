import requests
import re
from datetime import datetime

def obtener_datos_por_isbn(isbn):
    url = f"https://openlibrary.org/isbn/{isbn}.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return None
    except requests.exceptions.RequestException:
        return None

    data = response.json()
    titulo = data.get("title") or ""
    fecha = None
    anio = None

    publish_date = data.get("publish_date")
    if publish_date:
        try:
            fecha = datetime.strptime(publish_date, "%B %d, %Y").date()
            anio = fecha.year
        except ValueError:
            fecha = None
            for fmt in ("%B %Y", "%Y", "%b %Y", "%d %B %Y", "%B, %Y"):
                try:
                    dt = datetime.strptime(publish_date, fmt)
                    anio = dt.year
                    break
                except ValueError:
                    pass
            if anio is None:
                match = re.search(r"\b(1[0-9]{3}|20[0-9]{2}|21[0-9]{2})\b", publish_date)
                if match:
                    try:
                        anio = int(match.group(0))
                    except ValueError:
                        anio = None

    editorial = data.get("publishers", [None])[0]

    autor_nombre, autor_apellido, autor_bio = "", "", None
    if data.get("authors"):
        autor_key = data["authors"][0].get("key")
        if autor_key:
            autor_url = f"https://openlibrary.org{autor_key}.json"
            try:
                autor_resp = requests.get(autor_url, timeout=10)
                autor_resp.raise_for_status()
                autor_data = autor_resp.json()
                nombre_completo = autor_data.get("name", "").strip()
                partes = nombre_completo.split()
                autor_nombre = partes[0] if partes else ""
                autor_apellido = " ".join(partes[1:]) if len(partes) > 1 else ""
                autor_bio = autor_data.get("bio")
                if isinstance(autor_bio, dict):
                    autor_bio = autor_bio.get("value")
                elif not isinstance(autor_bio, str):
                    autor_bio = None
            except requests.exceptions.RequestException:
                pass

    return {
        "titulo": titulo,
        "fecha": fecha,
        "anio": anio,
        "isbn": isbn,
        "editorial": editorial or "",
        "autor": {
            "nombre": autor_nombre,
            "apellido": autor_apellido,
            "bibliografia": autor_bio or "",
        }
    }