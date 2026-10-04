# Terraform- und Provider-Versionen fixieren, damit der Aufbau reproduzierbar ist
terraform {
  required_version = ">= 1.6"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Der State liegt lokal (terraform.tfstate, per .gitignore ausgeschlossen).
  # SOLL für Teamarbeit: Remote State in einem Azure Storage Account.
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}
