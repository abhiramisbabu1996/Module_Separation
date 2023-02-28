from openerp import fields, models, api
from openerp.osv import fields as old_fields, osv, expression
import time
from datetime import datetime
import datetime


class project_modification(models.Model):
    _name = 'project.modification'
    
    name = fields.Char('Name')
    project_id = fields.Many2one('project.project')
    qty = fields.Float('Qty')
    rate = fields.Char('Rate')
    amount = fields.Float('Amount')
    remarks = fields.Text('Remarks')
    binary_field = fields.Binary('File')
    filename = fields.Char('Filename') 
    
    
class project(models.Model):
    _inherit = "project.project"
    
    modification_ids = fields.One2many('project.modification', 'project_id', 'Modification')