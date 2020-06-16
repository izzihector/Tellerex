from odoo import http
# from odoo.addons.web.controllers.main import Home
from odoo.http import request


# class Home(Home):
#     
#     def _login_redirect(self, uid, redirect=None):
#         if not redirect and request.env['res.users'].sudo().browse(uid).has_group('ticl_shipment_tender_ext.ticl_shipment_ext_group_user'):
#             base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
#             return base_url+'/web#action=251&model=ticl.shipment.log&view_type=list&menu_id=176'
#         return super(Home, self)._login_redirect(uid, redirect=redirect)
#     
class TenderImport(http.Controller):
    
    @http.route(['/import_tender',], type='http', auth="none", website=True)
    def customers(self, **post):
        if(post):
            print(post)
        return request.render("/", {})