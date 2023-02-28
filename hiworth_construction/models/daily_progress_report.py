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


class daily_progress_report(models.Model):
    _name = 'daily.progress.report'
    _order = 'date desc'
    
    
    
    name = fields.Char('Name')
    date = fields.Date('Date')
#     user_id = fields.Many2one('res.partner', 'Engineer', domain=[('customer','=',False),('supplier','=',False),
#                                                                 ('contractor','=',False)])
    remark = fields.Text('Remarks')
    dpr_line_ids = fields.One2many('daily.progress.report.line', 'report_id', 'Lines')
    inspect1 = fields.Many2one('hr.employee', 'Inspector1')
    inspect2 = fields.Many2one('hr.employee', 'Inspector2')
    inspect3 = fields.Many2one('hr.employee', 'Inspector3')
    inspect4 = fields.Many2one('hr.employee', 'Inspector4')
    
    _defaults = {
        'date': date.today()
        }
    
class daily_progress_report_line(models.Model):
    _name = 'daily.progress.report.line'
    
    @api.multi
    @api.onchange('date')
    def onchange_date(self):
        self.date = self.report_id.date
        
    name = fields.Char('Name')
    project_id = fields.Many2one('project.project', 'Project')
    partner_id = fields.Many2one('res.partner', 'Contractor', domain=[('contractor','=',True)])
    report_id = fields.Many2one('daily.progress.report', 'Report')
    date = fields.Date('Date')
#     activity = fields.Text('Name of the Work')
    qty1 = fields.Float('Qty')
    qty2 = fields.Float('Qty')
    qty3 = fields.Float('Qty')
    qty4 = fields.Float('Qty')
    category = fields.Char('Category')
    nos = fields.Float('Nos.')
    rate = fields.Char('Rate')
    amount = fields.Float('Amount')
    remarks = fields.Text('Remarks')


class daily_usage_report(models.Model):
    _name = 'daily.usage.report'



    READONLY_STATES = {
        'approved': [('readonly', True)],
    }

    name = fields.Char('Name',  states=READONLY_STATES)
    date = fields.Date('Date',  states=READONLY_STATES)
    journal_id = fields.Many2one('account.journal','Journal',  states=READONLY_STATES, domain=[('type','in',['cash','bank','general'])])
    line_ids = fields.One2many('daily.usage.report.line', 'report_id', 'Lines',  states=READONLY_STATES)
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ],default='draft')


    _defaults = {
        'date': fields.datetime.now(),

    }

    @api.multi
    def action_approve(self):
        self.ensure_one()
        move = self.env['account.move']
        move_line = self.env['account.move.line']
        for lines in self.line_ids:
            values = {
                'journal_id': lines.journal_id.id,
                'date': self.date,
                }
            move_id = move.create(values)
            values2 = {
                    'account_id': lines.account_id.id,
                    'name': 'Stock Movement' + ' ' + lines.product_id.name,
                    'debit': 0,
                    'credit': lines.inventory_value,
                    'move_id': move_id.id,
                    }
            line_id = move_line.create(values2)
            values3 = {
                    'account_id': lines.exp_account_id.id,
                    'name': 'Stock Movement' + ' ' + lines.product_id.name,
                    'debit': lines.inventory_value,
                    'credit': 0,
                    'move_id': move_id.id,
                    }
            line_id = move_line.create(values3)
            move_id.button_validate()

            estimation = self.env['project.task.estimation'].search([('task_id','=',lines.task_id.id),('pro_id','=',lines.product_id.id)])
            if estimation:
                estimation.qty_used = estimation.qty_used+lines.qty
        consumed_product_location = self.env.ref("hiworth_construction.stock_location_product_consumption").id
        move = self.env['stock.move']
        for transfer in self.line_ids:
            move_id = move.create({
                'name': transfer.product_id.name,
                'product_id': transfer.product_id.id,
                'restrict_lot_id': False,
                'product_uom_qty': transfer.qty,
                'product_uom': transfer.uom_id.id,
                'partner_id': self.user_id.partner_id.id,
                'location_id': transfer.location_id.id,
                'location_dest_id': consumed_product_location,
                'picking_id': False,
                'invoice-state': 'none',
                'date': self.date,

            })
            move_id.location_id = transfer.location_id.id
            move_id.action_done()
        self.state = 'approved'



class daily_usage_report_line(models.Model):
    _name = 'daily.usage.report.line'


    @api.multi
    @api.depends('product_id', 'qty', 'price_unit')
    def compute_invemtory_value(self):
        for line in self:
            line.inventory_value = line.qty * line.price_unit

    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.price_unit = self.product_id.standard_price
            self.uom_id = self.product_id.uom_id.id

    @api.onchange('project_id')
    def onchange_report(self):
        if self.report_id:
            self.journal_id = self.report_id.journal_id.id

    name = fields.Char('Name of the work')
    report_id = fields.Many2one('daily.usage.report', 'Report')
    project_id = fields.Many2one('project.project', 'Project')
    task_id = fields.Many2one('project.task', 'Task')
    product_id = fields.Many2one('product.product', 'Product')
    qty = fields.Float('Used Qty')
    uom_id = fields.Many2one('product.uom', 'Uom')
    price_unit = fields.Float('Unit Price')
    account_id = fields.Many2one('account.account', 'Asset Account')
    exp_account_id = fields.Many2one('account.account', 'Expense Account')
    journal_id = fields.Many2one('account.journal', 'Journal')
    inventory_value = fields.Float(compute='compute_invemtory_value', store=True, string="inventory Value")
    location_id = fields.Many2one('stock.location', 'Location')


    @api.model
    def create(self,vals):
        if vals.get('qty') == 0:
            raise osv.except_osv(_('Warning!'),_('Used Qty must be greater than zero'))

        return super(daily_usage_report_line, self).create(vals)