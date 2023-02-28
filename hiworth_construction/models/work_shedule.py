from openerp import fields, models, api
from openerp.osv import fields as old_fields, osv, expression
import time
from datetime import datetime
import datetime


class work_schedule(models.Model):
    _name = 'work.schedule'
    
    name = fields.Char('Name')
    project_id = fields.Many2one('project.project')
    schedule_line = fields.One2many('work.schedule.line', 'schedule_id', 'schedule Lines')
    
    
class work_schedule_line(models.Model):
    _name = 'work.schedule.line' 
    _order = "sequence, id"
    
    name = fields.Char('Name')
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")
    start_date = fields.Date('Start Date')
    end_date = fields.Date('Finish Date')
    status = fields.Char('Status')
    remarks = fields.Text('Remarks') 
    schedule_id = fields.Many2one('work.schedule', 'Schedule')
    
    
class project(models.Model):
    _inherit = "project.project"
    
    schedule_ids = fields.One2many('work.schedule', 'project_id', 'Project')