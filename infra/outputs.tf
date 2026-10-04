# Ausgaben nach "terraform apply"

output "app_url" {
  description = "Öffentliche URL der Autovermietung"
  value       = "https://${azurerm_container_app.web.ingress[0].fqdn}"
}

output "api_example" {
  description = "Beispielaufruf der Web-API"
  value       = "https://${azurerm_container_app.web.ingress[0].fqdn}/api/cars"
}

output "resource_group" {
  value = azurerm_resource_group.main.name
}

output "database_server" {
  value = azurerm_postgresql_flexible_server.main.fqdn
}
