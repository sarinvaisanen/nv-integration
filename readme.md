# Netvisor addon for Odoo 12

## Installation
Download repository as ZIP-file and decompress file contents to Odoo servers /addons-folder.

Use Odoos addon manager to install. Update addons list and search for "netvisor".

## Usage
Nothing fancy here. Pingpongs XML data back and forth. 

## Integrations
### Sales invoices
#### Create
Invoices are transferred to Netvisor individually with an push of a button. "Lähetä Netvisoriin" button is located in detailed invoice view.

#### Get sales invoice payments
Automatic process to update states and received payments of Odoo invoices.

Fetches all open sales invoices records from Odoo and maps them with new payment data from Netvisor.

### Purchase invoices
#### Sync to Odoo from Netvisor
Automatic process to create Odoo purchase invoices from Netvisor purchase invoices.

Creates new Odoo purchase invoice records out of Netvisor purchase invoice data.