from odoo import models, fields, api


class Settings(models.TransientModel):

    _inherit = 'res.config.settings'
    _name = 'netvisor.settings'

    # Netvisor access keys etc.
    auth_sender = fields.Char('Lähettäjän tunniste', required=True, readonly=False, help='Lähettäjän tunniste tooltip')
    
    auth_partner_id = fields.Char('Integraatiokumppanitunnus', required=True, readonly=False, help='Integraatiokumppanitunnus tooltip')
    auth_partner_key = fields.Char('Integraatiokumppaniavain', required=True, readonly=False, help='Integraatiokumppaniavain tooltip')
    auth_customer_id = fields.Char('Rajapintakäyttäjän käyttäjätunniste', required=True, readonly=False, help='Rajapintakäyttäjän käyttäjätunniste tooltip')
    company_registry_id = fields.Char('Netvisor-asiakkaan Y-tunnus (integraatioiden kohdeyritys)', required=True, readonly=False, help='Netvisor-asiakkaan Y-tunnus tooltip')
    authorization_key = fields.Char('Rajapintakäyttäjän käyttöoikeusavain (saatavilla/luotavissa Netvisorissa)', required=True, readonly=False, help='Rajapintakäyttäjän käyttöoikeusavain tooltip')
    
    # Netvisor general settings
    api_url = fields.Char('API URL', required=True, readonly=False, help='API URL tooltip')

    def get_values(self):
        res = super(Settings, self).get_values()
        res.update({
            'auth_sender': self.env['ir.config_parameter'].sudo().get_param('netvisor.auth_sender'),        
            'auth_partner_id': self.env['ir.config_parameter'].sudo().get_param('netvisor.auth_partner_id'),
            'auth_partner_key': self.env['ir.config_parameter'].sudo().get_param('netvisor.auth_partner_key'),
            'auth_customer_id': self.env['ir.config_parameter'].sudo().get_param('netvisor.auth_customer_id'),
            'company_registry_id': self.env['ir.config_parameter'].sudo().get_param('netvisor.company_registry_id'),
            'authorization_key': self.env['ir.config_parameter'].sudo().get_param('netvisor.authorization_key'),
            'api_url': self.env['ir.config_parameter'].sudo().get_param('netvisor.api_url')
        })
        return res

    def set_values(self):
        super(Settings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('netvisor.auth_sender', self.auth_sender)
        self.env['ir.config_parameter'].sudo().set_param('netvisor.auth_partner_id', self.auth_partner_id)
        self.env['ir.config_parameter'].sudo().set_param('netvisor.auth_partner_key', self.auth_partner_key)
        self.env['ir.config_parameter'].sudo().set_param('netvisor.auth_customer_id', self.auth_customer_id)
        self.env['ir.config_parameter'].sudo().set_param('netvisor.company_registry_id', self.company_registry_id)
        self.env['ir.config_parameter'].sudo().set_param('netvisor.authorization_key', self.authorization_key)
        self.env['ir.config_parameter'].sudo().set_param('netvisor.api_url', self.api_url)
