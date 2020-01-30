# -*- coding: utf-8 -*-
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from time import gmtime, strftime
import requests
import xmltodict
import json

from odoo.addons.netvisor.controllers import controllers
from odoo import api, fields, models

class NetvisorSalesPayment(models.Model):
    _name = 'account.payment'
    _inherit = 'account.payment'

    received_from_netvisor = fields.Boolean(
        'Kirjattu Netvisorissa?',
        required=False,
        default=False
    )
    
    received_from_netvisor_datetime = fields.Datetime(
        'Vastaanotettu Odooseen',
        required=False
    )
    
    netvisor_key = fields.Char(
        'Netvisor tunniste',
        required=False
    )
        
    
class NetvisorCustomer(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    # TODO: Integer should be used, BUT Netvisor customer ID doesn't fit into default integer definition.
    netvisor_customer_id = fields.Char(
        "Netvisor asiakaskoodi",
        required=False
    )
    
    netvisor_vendor_id = fields.Char(
        "Netvisor toimittajakoodi",
        required=False
    )

class NetvisorProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    # TODO: Integer should be used, BUT Netvisor product code doesn't fit into default integer definition.
    netvisor_product_id = fields.Char(
        "Netvisor tuotekoodi",
        required=False,
        default=0
    )

class NetvisorInvoice(models.Model):
    _name = 'account.invoice'
    _inherit = 'account.invoice'

    netvisor_delivered = fields.Boolean(
        "Lähetetty Netvisoriin?",
        default=False
    )

    netvisor_delivered_datetime = fields.Datetime(
        "Netvisor lähetysaika"
    )
    
    netvisor_invoice_number = fields.Char(
        'Netvisor laskunro'
    )

    netvisor_data_identifier = fields.Integer(
        "Netvisor tunniste"
    )
    
    '''
    @api.model
    def write(self, values):
        record = super(AccountInvoice, self).write(values)
        print(self)
        if (record.type is 'out_invoice' or record.type is 'out_refund') and record.netvisor_delivered is True and record.state is not 'paid':
            api_url = self.env['ir.config_parameter'].sudo(
            ).get_param('netvisor.api_url') 
            root = controllers.Netvisor.xml_from_sales_invoice(record)
            endpoint = f'{api_url}/salesinvoice.nv?method=edit'
            
       
            headers = self.refresh_headers(endpoint)
            response = requests.post(endpoint, headers=headers,
                data=ET.tostring(root))
            record = controllers.Netvisor.handle_send_invoice_response(response, record)
        
        return record
    '''

    @api.one
    def send_invoice_to_netvisor(self, args):
        
        self.unlink()

        # Load parameters from module configuration
        api_url = self.env['ir.config_parameter'].sudo(
        ).get_param('netvisor.api_url')

        # Should support three types of invoices: sales, purchase and credit (myyntilasku, ostolasku, hyvityslasku)
        record = self.browse([args.get('active_id')])
        record.ensure_one()

        invoice_type = args.get('type')

        # Sales invoice
        if invoice_type == 'out_invoice' or 'out_refund':
            root = controllers.Netvisor.xml_from_sales_invoice(record)
            endpoint = f'{api_url}/salesinvoice.nv?method=add'
            
       
            headers = self.refresh_headers(endpoint)
            response = requests.post(endpoint, headers=headers,
                data=ET.tostring(root))
            record = controllers.Netvisor.handle_send_invoice_response(response, record)
            
            endpoint = f'{api_url}/getsalesinvoice.nv?netvisorkey={record.netvisor_data_identifier}'
            headers = self.refresh_headers(endpoint)
            response = requests.get(endpoint, headers=headers, stream=False)
            
            # Fetch generated invoice from Netvisor and update Odoo invoice with some values.
            invoice_result = self.dump_and_load(response.text)
            netvisor_invoice = invoice_result['Root']['SalesInvoice']
            record.write({
                'netvisor_invoice_number': netvisor_invoice['SalesInvoiceNumber'],
                'reference': netvisor_invoice['SalesInvoiceReferencenumber']
            })
        
    @api.model
    def refresh_headers(self, endpoint):
        ''' Returns authentication headers for given endpoint'''
        common_headers = {
            'Content-Type': 'text/xml'
        }
        netvisor_headers = controllers.Netvisor.generate_auth_headers(self)
        headers = {**netvisor_headers, **common_headers}
        headers['X-Netvisor-Authentication-MAC'] = controllers.Netvisor.generate_mac(self, netvisor_headers, endpoint)
        return headers
    
    @api.model
    def dump_and_load(self, xml):
        xml_to_json = json.dumps(xmltodict.parse(xml))
        json_to_dict = json.loads(xml_to_json)
        return json_to_dict
    
    @api.model
    def parse_sales_invoices_from(self, data):
        if 'SalesInvoices' in data.get('Root'):
            [netvisor_invoices] = list(data['Root']['SalesInvoices'].values())
        
        if 'SalesInvoice' in data.get('Root'):
            data['Root']['SalesInvoices'] = {}
            data['Root']['SalesInvoices']['SalesInvoice'] = {}
            data['Root']['SalesInvoices']['SalesInvoice'] = data['Root']['SalesInvoice']
            netvisor_invoices = list(data['Root']['SalesInvoices'].values())
            
        return netvisor_invoices
    
    @api.model
    def parse_purchase_invoices_from(self, data):
        if 'PurchaseInvoiceList' in data.get('Root'):
            netvisor_invoices = list(data['Root']['PurchaseInvoiceList'].values())
        
        return netvisor_invoices
    
    @api.model
    def map_netvisor_payments_to_netvisor_invoices(self, netvisor_invoices, netvisor_payments):
        mapped = []
        for invoice in netvisor_invoices:
            payments = list(filter(lambda payment: payment['InvoiceNumber'] == invoice['SalesInvoiceNumber'], netvisor_payments))
            if len(payments) > 0:
                invoice['MappedPayments'] = payments
                mapped.append(invoice)
            else:
                del invoice
                
        return mapped
        
        
    @api.multi
    def get_purchase_invoices(self, args):
        
        self.unlink()
        
        api_url = self.env['ir.config_parameter'].sudo(
        ).get_param('netvisor.api_url')
        
        # Fetch Netvisor invoices
        endpoint = f'{api_url}/purchaseinvoicelist.nv' # ?lastmodifiedstart=something
        headers = self.refresh_headers(endpoint)
        response = requests.get(endpoint, headers=headers, stream=False)
        invoices_result = self.dump_and_load(response.text)
        netvisor_invoices = self.parse_purchase_invoices_from(invoices_result)
        
        # First check if we are creating or updating an Odoo record
        if len(netvisor_invoices) == 0:
            raise Exception("Nothing to do")
        
        for netvisor_invoice_summary in netvisor_invoices:
            # Fetch invoice details from Netvisor
            endpoint =  netvisor_invoice_summary['Uri']
            headers = self.refresh_headers(endpoint)
            response = requests.get(endpoint, headers=headers, stream=False)
            invoice_result = self.dump_and_load(response.text)
            full_netvisor_invoice = invoice_result['Root']['PurchaseInvoice']
            print('Details p invoice', full_netvisor_invoice)
        
            # TODO: Netvisor documentation states that 'InvoiceStatus' field always returns 'open'
            # as the API is still under construction. Yet, 'Avoin' value has also been encountered.
            state_map = {
                'Avoin': 'open'
            }
            invoice_delivery_date = full_netvisor_invoice['PurchaseInvoiceDeliveryDate']['#text']
            invoice_date = full_netvisor_invoice['PurchaseInvoiceDate']['#text']
            invoice_due_date = full_netvisor_invoice['PurchaseInvoiceDueDate']['#text']
            total_amount = float(str(full_netvisor_invoice['PurchaseInvoiceAmount']).replace(",", "."))
            print('Total', total_amount)
            
            # TODO: Resolve partner
            netvisor_vendor_id =  full_netvisor_invoice['VendorCode']
            partner_record = self.env['res.partner'].search([('netvisor_vendor_id', '=', netvisor_vendor_id)], limit=1)
            partner_record.ensure_one()
            
            print('Partner', partner_record)
                        
            # Check if Odoo record exists
            record = self.search([
                ('type', '=', 'in_invoice'),
                ('netvisor_data_identifier', '=', netvisor_invoice_summary['NetvisorKey']),
                ('netvisor_invoice_number', '=', netvisor_invoice_summary['InvoiceNumber']), 
            ], limit=1)
            
            fields = {
                'type': 'in_invoice',
                'reference': full_netvisor_invoice['PurchaseInvoiceReferencenumber'],
                'number': full_netvisor_invoice['PurchaseInvoiceNumber'],
                'state': 'draft',
                'date': invoice_delivery_date,
                'date_invoice': invoice_date,
                'date_due': invoice_due_date,
                'amount_total': total_amount,
                'currency_id': 1,
                'journal_id': 2, # 2 = Vendor bills
                'company_id': 1,
                'netvisor_data_identifier': full_netvisor_invoice['PurchaseInvoiceNetvisorKey'],
                'netvisor_invoice_number': full_netvisor_invoice['PurchaseInvoiceNumber'],
                'account_id': 13, # 13 = Account payable
                'partner_id': partner_record.id
            }
            
            if record.id:
                record.write(fields)
            else:
                record.create(fields)
                
            # Generate invoice lines
            invoice_lines = list(full_netvisor_invoice['InvoiceLines'].values())
            if len(invoice_lines) > 0:
                for invoice_line in invoice_lines:
                    if invoice_line is not None:
                        
                        product_name = invoice_line['ProductName'] if invoice_line['ProductName'] is not None else 'Nimike puuttuu'
                        
                        record.invoice_line_ids.unlink()
                        
                        invoice_line_record = record.invoice_line_ids.create({
                            'invoice_id': record.id,
                            'name': product_name,
                            'account_id': 17,
                            'price_unit': float(str(invoice_line['UnitPrice']).replace(",", ".")),
                            'price_subtotal': float(str(invoice_line['LineSum']).replace(",", ".")),
                            'quantity': invoice_line['OrderedAmount'],
                            'uom_id': 1,
                            'company_id': 1,
                            'partner_id': partner_record.id,
                            'account_id': 17, # 17 = Product sales,
                            'discount': invoice_line['DiscountPercentage']
                        })
                        print('Invoice line', invoice_line_record)
                
            record.compute_taxes()
            record.state = 'open'
            print('Result', record)
            

        print('Purchase invoices', netvisor_invoices)
    
    @api.multi  
    def sync_sales_payments(self, args):
        
        self.unlink()
        
        records = self.search([('type', '=', 'out_invoice'), ('state', '=', 'open'), ('netvisor_delivered', '=', True)])
        
        if not records.exists():
            raise Exception("Nothing to do")
                    
        # Generate ID list of Netvisor invoices that will be fetched.
        # Netvisor invoice fetch required 'cause Netvisor payments use Invoice.SalesInvoiceNumber as reference...
        # ...and Invoice.SalesInvoiceNumber is not returned when creating new Invoice to Netvisor.
        # So in our invoice model we have Netvisor key that is used to fetch invoice number.  
        netvisor_keys = []
        for record in records:
            netvisor_keys.append(str(record.netvisor_data_identifier))
        
        netvisor_keys = ','.join(netvisor_keys)
                       
        api_url = self.env['ir.config_parameter'].sudo(
        ).get_param('netvisor.api_url')
        
        # Fetch Netvisor invoices
        endpoint = f'{api_url}/getsalesinvoice.nv?netvisorkeylist={netvisor_keys}'
        headers = self.refresh_headers(endpoint)
        response = requests.get(endpoint, headers=headers, stream=False)
        
        # As Netvisor continues to suck donkey balls, we need to struggle a little bit.
        # getsalesinvoice endpoint returns multiple results as list and single result as object.
        invoices_result = self.dump_and_load(response.text)
        netvisor_invoices = self.parse_sales_invoices_from(invoices_result)
        
        if netvisor_invoices is None or len(netvisor_invoices) == 0:
            raise Exception("No matching invoices in Netvisor")
        
        # Fetch invoice payments
        endpoint = f'{api_url}/salespaymentlist.nv?limitlinkedpayments=1' # &abovenetvisorkey=previoussynclastitem
        headers = self.refresh_headers(endpoint)
        response = requests.get(endpoint, headers=headers, stream=False)
        payments_result = self.dump_and_load(response.text)
        netvisor_payments_list = payments_result['Root']['SalesPaymentList']
        
        if payments_result is None or netvisor_payments_list is None:
            raise Exception("No payments in Netvisor")
        
        netvisor_payments = list(payments_result['Root']['SalesPaymentList'].values())
        if isinstance(netvisor_payments[0], list):
            [netvisor_payments] = netvisor_payments
        # print('net', netvisor_payments)
                                    
        # Map payments to invoices, as Netvisor API does not support "fetch payment by invoice" kind of operations
        netvisor_invoices_with_payments = self.map_netvisor_payments_to_netvisor_invoices(netvisor_invoices, netvisor_payments)
            
        # TODO: Generate AccountPayment entities out of mapped Netvisor data
        print('Mapped Netvisor invoices', len(netvisor_invoices_with_payments), netvisor_invoices_with_payments)
        for netvisor_invoice in netvisor_invoices_with_payments:
            odoo_invoice = self.search([
                ('netvisor_data_identifier', '=', int(netvisor_invoice['SalesInvoiceNetvisorKey']))
            ], limit=1)
            
            if netvisor_invoice['MappedPayments'] != False:
                for netvisor_payment in netvisor_invoice['MappedPayments']:
                    
                    # TODO: Handle credit loss - netvisor_payment['Name'] == 'Luottotappio'. Doable?
                    # For now, skip handling
                    # Also skip handling of payments with undefined payment method
                    
                    if netvisor_payment['Name'] == 'Luottotappio' or netvisor_payment['PaymentAccountName'] is None:
                        continue
                    
                    payment_date = datetime.strptime(netvisor_payment['Date'], '%d.%m.%Y').strftime('%Y-%m-%d')
                    payment_account_name = netvisor_payment['PaymentAccountName'].lower()
                    payment_method_map = {
                        'stripe': 3, # 
                        'nordea': 1, # 
                        'pankkikortti': 3, # inbound electronic
                        'käteinen': 1 # inbound manual
                    }
                    
                    odoo_payment_data = {
                        'name': netvisor_payment['Name'],
                        'state': 'draft',
                        'payment_type': 'inbound', # Required
                        'payment_reference': netvisor_payment['ReferenceNumber'],
                        'payment_method_id': payment_method_map[payment_account_name], # Required 
                        'amount': abs(float(str(netvisor_payment['Sum']).replace(",", "."))), # Required
                        'currency_id': 1, # Required
                        'payment_date': payment_date, # Required
                        'journal_id': record.journal_id.id, # Required
                        'received_from_netvisor': True,
                        'received_from_netvisor_datetime': datetime.now(),
                        'netvisor_key': netvisor_payment['NetvisorKey'],
                        'partner_type': 'customer',
                        'partner_id': odoo_invoice.partner_id.id
                    }
                            
                    odoo_payment = self.env['account.payment'].create(odoo_payment_data)
                    
                    odoo_payment.invoice_ids = odoo_invoice

                    if odoo_invoice.state == 'open':
                        odoo_payment.post()
                    