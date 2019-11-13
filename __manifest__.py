# -*- coding: utf-8 -*-
{
    'name': "Netvisor integrations",

    'summary': "Manually triggered Netvisor actions for sales invoices",

    'description': "",

    'author': "Reason Oy",
    'website': "https://reason.fi",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Invoicing &amp; Payments',
    'version': '0.4',

    # any Odoo module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    
    # External dependencies
    
    'external_dependencies': {
        'python': [
            'xmltodict'
        ]
    }
}
