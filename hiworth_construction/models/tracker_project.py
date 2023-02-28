from openerp import fields, models, api

class TrackerProjectStatus(models.Model):
    _name = 'tracker.project.status'
    _rec_name = 'project_id'

    project_id = fields.Many2one('project.project',"Project")
    location_id = fields.Many2one('stock.location',"Location")
    date = fields.Date("Date")
    document_no = fields.Char("Document No")
    document_id = fields.Many2one('document.document',"Document")
    status_id = fields.Many2one('document.status',"Status")
    remarks = fields.Char("Remarks")
    tracker_ids = fields.One2many('tracker.project.status.line','tracker_project_status_id',"Tracker")

class TrackerProjectStatusLine(models.Model):
    _name = 'tracker.project.status.line'

    date = fields.Date("Date")
    document_no = fields.Char("Document No")
    document_id = fields.Many2one('document.document', "Document")
    status_id = fields.Many2one('document.status', "Status")
    remarks = fields.Char("Remarks")
    tracker_project_status_id = fields.Many2one('tracker.project.status',"Tracker Project")





