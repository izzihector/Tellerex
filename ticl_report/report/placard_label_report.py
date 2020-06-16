from odoo import api, models

class ParticularReport(models.AbstractModel):
    _name = 'report.ticl_report.report_placards_label'


    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('ticl_report.report_placards_label')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
        }
        return report_obj.render('ticl_report.report_placards_label', docargs)


class ParticularIndividualReport(models.AbstractModel):
    _name = 'report.ticl_report.report_placards_labels_individual'

    @api.model
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('ticl_report.report_placards_labels_individual')
        docargs = {
            'doc_ids': docids,
            'doc_model': report.model,
            'docs': self,
        }
        return report_obj.render('ticl_report.report_placards_labels_individual', docargs)




