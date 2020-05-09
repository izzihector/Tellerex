# -*- coding: utf-8 -*-


from odoo import api, fields, models, _
import calendar
from datetime import datetime, timedelta, date


class AccountAgedTrialBalance(models.TransientModel):
    _name = 'monthly.fright.invoice'

    def _get_current_yr_months(self):
        current_year = date.today().year
        selection_list = []
        for month_val in range(1, 13):
            mn = calendar.month_name[month_val]+'-'+str(current_year)
            xy = mn.title()
            x = str(month_val)+'-'+str(current_year)
            selection_list.append((x,xy))
        return selection_list
    
    def _get_current_select(self):
        month = date.today().month
        year = date.today().year
        x = str(month)+'-'+str(year)
        return x
    
    invoice_type = fields.Selection([('monthly', 'Service Invoice'), ('fright', 'Freight Invoice')],string='Invoice Type')
    months = fields.Selection(selection=_get_current_yr_months, string='Month',default=_get_current_select)
    
    def generate_invoice(self):
        print(self.invoice_type)
        action = self.env['account.move'].monthly_fright_invoice({'type':self.invoice_type,'month':self.months})
        return action

