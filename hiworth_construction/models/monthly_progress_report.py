from openerp import fields, models, api
from openerp.osv import fields as old_fields, osv, expression
import time
from datetime import datetime
import datetime
from openerp.exceptions import except_orm, Warning, RedirectWarning
#from openerp.osv import fields
from openerp import tools
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from pychart.arrow import default
from cookielib import vals_sorted_by_key
# from pygments.lexer import _default_analyse
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
# from openerp.osv import osv
from openerp import SUPERUSER_ID

from lxml import etree

# 
class DProgress_Report_line(models.Model):
    _name = 'progress.report.line'

    name = fields.Char('Name')
#     date = fields.Date('Date')
    project_id = fields.Many2one(related='report_id.project_id', store=True, string='Project')
    work_planned = fields.Text('Work Planned')
    work_done = fields.Text('Work Done')
    reason = fields.Text('Reason for Delay')
    remarks = fields.Text('Remarks')
    report_id = fields.Many2one('progress.report', 'Report')


class Progress_Report(models.Model):
    _name = 'progress.report'
    _order = 'project_id desc'
    
    name = fields.Char('Name')
    project_id = fields.Many2one('project.project', 'Project')
    report_line_ids = fields.One2many('progress.report.line', 'report_id', 'Lines')
    remark = fields.Text('Remarks')
    month = fields.Selection([('jan', 'January'),('feb', 'February'),('mar', 'March'),('apr', 'April'),
                                   ('may', 'May'),('jun', 'June'),('jul', 'July'),('aug', 'August'),
                                   ('sep', 'September'),('oct', 'October'),('nov', 'November'),('dec', 'December')
                                   ], 'Month', select=True, copy=False)


                                   
                                   