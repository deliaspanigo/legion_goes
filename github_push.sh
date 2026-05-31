# 1. Preparar los archivos (Aseguramos que todo lo nuevo esté incluido)
git add .

# 2. Confirmar los cambios con un mensaje profesional
git commit -m "Release v0.1.0: Big Fix"

# 3. Crear la etiqueta (Tag) oficial de la versión
git tag -a v0.1.0 -m "Big Fix"

# 4. Subir el código a la rama principal
git push origin main

# 5. Subir la etiqueta a GitHub (Esto activa la sección 'Releases')
git push origin v0.1.0
