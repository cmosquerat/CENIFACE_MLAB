# Comando Docker Run para PowerShell (versión simple)
# Copia y pega este comando en PowerShell
# NOTA: El proxy se configura a nivel de Docker Desktop (transparente)

$currentDir = Get-Location

docker run -d `
  --name multilab-agroanalitica `
  --restart=unless-stopped `
  -p 127.0.0.1:5005:5000 `
  --env-file .env `
  -v "${currentDir}\multilab.db:/app/multilab.db:ro" `
  -v "${currentDir}\static\pdfs:/app/static/pdfs" `
  multilab-agroanalitica:latest

