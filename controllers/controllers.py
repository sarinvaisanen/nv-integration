# -*- coding: utf-8 -*-
import xml.etree.ElementTree as ET
import hashlib
import uuid

from datetime import datetime
from time import gmtime, strftime
from odoo import http


class Netvisor(http.Controller):

    @staticmethod
    def generate_mac(self, headers, endpoint):
        auth_partner_key = self.env['ir.config_parameter'].sudo(
        ).get_param('netvisor.auth_partner_key')
        
        authorization_key = self.env['ir.config_parameter'].sudo(
        ).get_param('netvisor.authorization_key')

        hashable = endpoint + '&'
        hashable += headers['X-Netvisor-Authentication-Sender'] + '&'
        hashable += headers['X-Netvisor-Authentication-CustomerId'] + '&'
        hashable += headers['X-Netvisor-Authentication-Timestamp'] + '&'
        hashable += headers['X-Netvisor-Interface-Language'] + '&'
        hashable += headers['X-Netvisor-Organisation-ID'] + '&'
        hashable += headers['X-Netvisor-Authentication-TransactionId'] + '&'
        hashable += authorization_key + '&'
        hashable += auth_partner_key
        hash_object = hashlib.sha256(hashable.encode('utf-8'))
        hex_dig = hash_object.hexdigest()
        print('Generated hashable', hashable)
        print('Generated MAC', hex_dig)
        return hex_dig
    
    @staticmethod
    def generate_auth_headers(self):
        # Load parameters from module configuration
        auth_sender = self.env['ir.config_parameter'].sudo(
        ).get_param('netvisor.auth_sender')
        
        auth_partner_id = self.env['ir.config_parameter'].sudo(
        ).get_param('netvisor.auth_partner_id')
        
        auth_customer_id = self.env['ir.config_parameter'].sudo(
        ).get_param('netvisor.auth_customer_id')
        
        company_registry_id = self.env['ir.config_parameter'].sudo(
        ).get_param('netvisor.company_registry_id')
        
        netvisor_headers = {
            'X-Netvisor-Authentication-Sender': auth_sender,
            'X-Netvisor-Authentication-CustomerId': auth_customer_id,
            'X-Netvisor-Authentication-PartnerId': auth_partner_id,
            'X-Netvisor-Authentication-Timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'X-Netvisor-Authentication-TransactionId': str(uuid.uuid4()),
            'X-Netvisor-Interface-Language': 'FI',
            'X-Netvisor-Organisation-ID': company_registry_id,
            'X-Netvisor-Authentication-MAC': '',
            'X-Netvisor-Authentication-MACHashCalculationAlgorithm': 'SHA256'
        }
        return netvisor_headers
      

    @staticmethod
    def xml_from_purchase_invoice(record):
        ''' TODO: Remove. Not needed. Purchase invoices are managed in Netvisor '''
        root = ET.Element('root')
        date_format = "%Y-%m-%d"

        print('Sending purchase invoice to Netvisor', record)

        # Create the XML structure
        purchaseinvoice = ET.SubElement(root, 'purchaseinvoice')

        invoicenumber = ET.SubElement(purchaseinvoice, 'invoicenumber')
        invoicenumber.text = record.number

        invoicedate = ET.SubElement(purchaseinvoice, 'invoicedate')
        invoicedate.set('format', 'ansi')
        invoicedate.set('findopendate', 'true')
        invoicedate.text = str(record.date_invoice.strftime(date_format))

        invoicesource = ET.SubElement(purchaseinvoice, 'invoicesource')
        invoicesource.text = 'manual'

        valuedate = ET.SubElement(purchaseinvoice, 'valuedate')
        valuedate.set('format', 'ansi')
        valuedate.text = str(record.date_invoice.strftime(date_format))

        duedate = ET.SubElement(purchaseinvoice, 'duedate')
        duedate.set('format', 'ansi')
        duedate.text = str(record.date_due.strftime(date_format))

        purchaseinvoiceonround = ET.SubElement(purchaseinvoice, 'purchaseinvoiceonround')
        purchaseinvoiceonround.set('type', 'netvisor')
        # TODO: Map state
        purchaseinvoiceonround.text = 'open'

        vendorcode = ET.SubElement(purchaseinvoice, 'vendorcode')
        vendorcode.text = str(record.partner_id.id)

        vendorname = ET.SubElement(purchaseinvoice, 'vendorname')
        vendorname.text = record.partner_id.name

        vendoraddressline = ET.SubElement(purchaseinvoice, 'vendoraddressline')
        vendoraddressline.text = record.partner_id.street

        vendorpostnumber = ET.SubElement(purchaseinvoice, 'vendorpostnumber')
        vendorpostnumber.text = record.partner_id.zip

        vendorcity = ET.SubElement(purchaseinvoice, 'vendorcity')
        vendorcity.text = record.partner_id.city

        vendorcountry = ET.SubElement(purchaseinvoice, 'vendorcountry')
        vendorcountry.text = record.partner_id.country_id.code

        vendorphonenumber = ET.SubElement(purchaseinvoice, 'vendorphonenumber')
        vendorphonenumber.text = record.partner_id.phone

        vendorfaxnumber = ET.SubElement(purchaseinvoice, 'vendorfaxnumber')
        vendorfaxnumber.text = ''

        vendoremail = ET.SubElement(purchaseinvoice, 'vendoremail')
        vendoremail.text = record.partner_id.email

        vendorhomepage = ET.SubElement(purchaseinvoice, 'vendorhomepage')
        vendorhomepage.text = record.partner_id.website

        amount = ET.SubElement(purchaseinvoice, 'amount')
        amount.text = str(record.amount_total_signed)

        accountnumber = ET.SubElement(purchaseinvoice, 'accountnumber')
        accountnumber.text = record.partner_bank_id.sanitized_acc_number

        organizationidentifier = ET.SubElement(purchaseinvoice, 'organizationidentifier')
        organizationidentifier.text = str(record.partner_id.company_id.id)

        overduefinepercent = ET.SubElement(purchaseinvoice, 'overduefinepercent')
        overduefinepercent.text = ''

        bankreferencenumber = ET.SubElement(purchaseinvoice, 'bankreferencenumber')
        bankreferencenumber.text = record.partner_bank_id.bank_id.bic

        ourreference = ET.SubElement(purchaseinvoice, 'ourreference')
        ourreference.text = record.reference

        yourreference = ET.SubElement(purchaseinvoice, 'yourreference')
        yourreference.text = ''

        currencycode = ET.SubElement(purchaseinvoice, 'currencycode')
        currencycode.text = record.currency_id.name

        deliveryterms = ET.SubElement(purchaseinvoice, 'deliveryterms')
        deliveryterms.text = ''

        deliverymethod = ET.SubElement(purchaseinvoice, 'deliverymethod')
        deliverymethod.text = ''

        comment = ET.SubElement(purchaseinvoice, 'comment')
        comment.text = record.comment

        checksum = ET.SubElement(purchaseinvoice, 'checksum')
        checksum.text = ''

        pdfextrapages = ET.SubElement(purchaseinvoice, 'pdfextrapages')
        pdfextrapages.text = ''

        readyforaccounting = ET.SubElement(purchaseinvoice, 'readyforaccounting')
        readyforaccounting.text = ''

        primaryvendormatchtype = ET.SubElement(purchaseinvoice, 'primaryvendormatchtype')
        primaryvendormatchtype.text = ''

        # Purchase invoice lines
        purchaseinvoicelines = ET.SubElement(purchaseinvoice, 'purchaseinvoicelines')

        for line in record.invoice_line_ids: 
            # Single line
            purchaseinvoiceline = ET.SubElement(purchaseinvoicelines, 'purchaseinvoiceline')

            productcode = ET.SubElement(purchaseinvoiceline, 'productcode')
            productcode.text = str(line.product_id.id)

            productname = ET.SubElement(purchaseinvoiceline, 'productname')
            productname.text = line.name

            orderedamount = ET.SubElement(purchaseinvoiceline, 'orderedamount')
            orderedamount.text = str(line.quantity)

            deliveredamount = ET.SubElement(purchaseinvoiceline, 'deliveredamount')
            deliveredamount.text = ''

            unitname = ET.SubElement(purchaseinvoiceline, 'unitname')
            unitname.text = line.uom_id.name

            unitprice = ET.SubElement(purchaseinvoiceline, 'unitprice')
            unitprice.text = str(line.price_unit)

            discountpercentage = ET.SubElement(purchaseinvoiceline, 'discountpercentage')
            discountpercentage.text = str(line.discount)

            vatpercent = ET.SubElement(purchaseinvoiceline, 'vatpercent')
            vatpercent.text = next((str(x.tax_id.amount) for x in record.tax_line_ids if x.id == line.id), '24')

            linesum = ET.SubElement(purchaseinvoiceline, 'linesum')
            linesum.set('type', 'brutto')
            linesum.text = str(line.price_subtotal_signed)

            description = ET.SubElement(purchaseinvoiceline, 'description')
            description.text = ''

            sort = ET.SubElement(purchaseinvoiceline, 'sort')
            sort.text = ''

            accountingsuggestion = ET.SubElement(purchaseinvoiceline, 'accountingsuggestion')
            accountingsuggestion.text = ''

            '''
            dimension = ET.SubElement(purchaseinvoiceline, 'dimension')

            dimensionVolumeName = ET.SubElement(dimension, 'dimensionname')
            dimensionVolumeName.text = 'volume'

            dimensionVolumeItem = ET.SubElement(dimension, 'dimensionitem')
            dimensionVolumeItem.text = str(line.product_id.volume)

            dimensionWeightName = ET.SubElement(dimension, 'dimensionname')
            dimensionWeightName.text = 'weight'

            dimensionWeightItem = ET.SubElement(dimension, 'dimensionitem')
            dimensionWeightItem.text = str(line.product_id.weight)
            '''

        return root

    @staticmethod
    def xml_from_sales_invoice(record):
        root = ET.Element('root')
        date_format = "%Y-%m-%d"

        print('Sending sales invoice to Netvisor', record)

        # Create the XML structure
        salesInvoice = ET.SubElement(root, 'salesinvoice')

        # Sales invoice fields

        # Integer if given. Netvisor generated if absent.
        # salesInvoiceNumber = ET.SubElement(salesInvoice, 'salesinvoicenumber')
        # salesInvoiceNumber.text = record.number 

        salesInvoiceDate = ET.SubElement(salesInvoice, 'salesinvoicedate')
        salesInvoiceDate.set('format', 'ansi')        
        salesInvoiceDate.text = str(record.date_invoice.strftime(date_format))

        salesInvoiceDueDate = ET.SubElement(salesInvoice, 'salesinvoiceduedate')
        salesInvoiceDueDate.set('format', 'ansi')
        salesInvoiceDueDate.text = str(record.date_due.strftime(date_format))

        salesInvoiceDeliveryDate = ET.SubElement(salesInvoice, 'salesinvoicedeliverydate')
        salesInvoiceDeliveryDate.set('format', 'ansi')
        salesInvoiceDeliveryDate.text = ''


        # TODO: Mapping
        statuses = {
            'draft': 'draft',
            'open': 'open',
            'in_payment': 'in_payment',
            'paid': 'paid',
            'cancel': 'cancel'
        }

        # Not required. Reference number format if given.
        salesInvoiceReferenceNumber = ET.SubElement(salesInvoice, 'salesinvoicereferencenumber')
        salesInvoiceReferenceNumber.text = '12 34561' # str(record.reference)

        salesInvoiceAmount = ET.SubElement(salesInvoice, 'salesinvoiceamount')
        salesInvoiceAmount.text = str(record.amount_untaxed_signed)

        # Not required. Defaults to 'invoice'
        invoiceTypes = {
            'out_invoice': 'invoice',
            'in_invoice': 'order'
        }
        invoiceType = ET.SubElement(salesInvoice, 'invoicetype')
        invoiceType.text = invoiceTypes.get(record.type)

        # salesInvoiceFreeTextBeforeLines = ET.SubElement(salesInvoice, 'salesInvoiceFreeTextBeforeLines')
        # salesInvoiceFreeTextBeforeLines.text = record.comment

        salesInvoiceStatus = ET.SubElement(salesInvoice, 'salesinvoicestatus')
        salesInvoiceStatus.set('type', 'netvisor')
        salesInvoiceStatus.text = statuses.get(record.state)

        # Referenced value must exist in Netvisors invoicing customer records.
        invoicingCustomeridentifier = ET.SubElement(salesInvoice, 'invoicingcustomeridentifier')
        invoicingCustomeridentifier.set('type', 'customer')
        invoicingCustomeridentifier.text = str(record.partner_id.netvisor_customer_id)

        '''
        # Invoicing customer fields given only if invoicingcustomeridentifier absent.
        invoicingCustomerName = ET.SubElement(salesInvoice, 'invoicingcustomername')
        invoicingCustomerName.text = record.partner_id.name

        invoicingCustomerNameExtension = ET.SubElement(salesInvoice, 'invoicingCustomerNameExtension')
        invoicingCustomerNameExtension.text = record.partner_id.commercial_company_name

        invoicingCustomerAddressLine = ET.SubElement(salesInvoice, 'invoicingCustomerAddressLine')
        invoicingCustomerAddressLine.text = record.partner_id.street

        invoicingCustomerAdditionalAddressLine = ET.SubElement(salesInvoice, 'invoicingCustomerAdditionalAddressLine')
        invoicingCustomerAdditionalAddressLine.text = record.partner_id.street2

        invoicingCustomerPostNumber = ET.SubElement(salesInvoice, 'invoicingCustomerPostNumber')
        invoicingCustomerPostNumber.text = record.partner_id.zip

        invoicingCustomerTown = ET.SubElement(salesInvoice, 'invoicingCustomerTown')
        invoicingCustomerTown.text = record.partner_id.city

        invoicingCustomerCountryCode = ET.SubElement(salesInvoice, 'invoicingCustomerCountryCode')
        invoicingCustomerCountryCode.text = record.partner_id.country_id.code
        '''
        

        # Invoice lines
        invoice_lines = ET.SubElement(salesInvoice, 'invoicelines')

        for line in record.invoice_line_ids:
            invoiceLine = ET.SubElement(invoice_lines, 'invoiceLine')
            salesInvoiceProductLine = ET.SubElement(invoiceLine, 'salesinvoiceproductline')

            productIdentifier = ET.SubElement(salesInvoiceProductLine, 'productidentifier')
            productIdentifier.set('type', 'customer')
            productIdentifier.text = str(line.product_id.netvisor_product_id)

            productName = ET.SubElement(salesInvoiceProductLine, 'productname')
            productName.text = line.name

            productunitPrice = ET.SubElement(salesInvoiceProductLine, 'productunitprice')
            productunitPrice.set('type', 'net')
            productunitPrice.text = str(line.price_unit)

            productVatPercentage = ET.SubElement(salesInvoiceProductLine, 'productvatpercentage')
            productVatPercentage.set('vatcode', 'KOMY')
            
            vatPercentage = record.invoice_line_ids.invoice_line_tax_ids.amount
            productVatPercentage.text = str(vatPercentage)

            salesInvoiceProductLineQuantity = ET.SubElement(salesInvoiceProductLine, 'salesinvoiceproductlinequantity')
            salesInvoiceProductLineQuantity.text = str(line.quantity)

            """
            dimension = ET.SubElement(salesInvoiceProductLine, 'dimension')

            dimensionVolumeName = ET.SubElement(dimension, 'dimensionname')
            dimensionVolumeName.text = 'volume'

            dimensionVolumeItem = ET.SubElement(dimension, 'dimensionitem')
            dimensionVolumeItem.text = str(line.product_id.volume)

            dimensionWeightName = ET.SubElement(dimension, 'dimensionname')
            dimensionWeightName.text = 'weight'

            dimensionWeightItem = ET.SubElement(dimension, 'dimensionitem')
            dimensionWeightItem.text = str(line.product_id.weight)
            """


        # TODO: Check XML naming invoiceLine/invoiceline. Smells fishy.
        if record.comment:
            comment_line = ET.Element('invoiceline')

            sales_invoice_comment_line = ET.SubElement(comment_line, 'salesinvoicecommentline')

            comment = ET.SubElement(sales_invoice_comment_line, 'comment')
            comment.text = record.comment

            invoice_lines.append(comment_line)

        # TODO: Invoice voucher lines? Meaning?

        return root
    
    
    @staticmethod
    def handle_send_invoice_response(response, record):
        # Handle result
        print(response.text)
        result_root = ET.fromstring(response.text)
        response_status = result_root.find('ResponseStatus').find('Status')
            
        if response and response_status.text == 'OK':
            record.write({
                'netvisor_delivered': True,
                'netvisor_delivered_datetime': datetime.now(),
                'netvisor_data_identifier': result_root.find('Replies').find('InsertedDataIdentifier').text
            })
            return record
        else:
            # TODO: Log this shit
            raise Exception(result_root.find('ResponseStatus')[1].text)
        
        
    @staticmethod
    def get_sales_payment_list(self):
        print('Fetching sales payments')
        
        
   
        
