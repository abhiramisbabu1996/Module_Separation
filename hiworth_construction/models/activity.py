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


class ProjectProject(models.Model):
    _inherit = 'project.project'

    @api.constrains('name')
    def _check_duplicate_name(self):
        names = self.search([])
        for c in names:
            if self.id != c.id:
                if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(" ", ""):
                    raise osv.except_osv(_('Error!'), _('Error: project name must be unique'))
            else:
                pass


class ProjectTask(models.Model):
    _inherit = 'project.task'

    @api.constrains('name')
    def _check_duplicate_name(self):
        names = self.search([])
        for c in names:
            if self.id != c.id:
                if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(" ", ""):
                    raise osv.except_osv(_('Error!'), _('Error: name must be unique'))
            else:
                pass

class HrEmployee(models.Model):
    _inherit = 'hr.employee'


    @api.constrains('name')
    def _check_duplicate_name(self):
        names = self.search([])
        for c in names:
            if self.id != c.id:
                if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(" ", ""):
                    raise osv.except_osv(_('Error!'), _('Error: employee name must be unique'))
            else:
                pass

                

    current_location_id = fields.Many2one('stock.location', 'Current Working Site')

    

class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.constrains('name')
    def _check_duplicate_name(self):
        names = self.search([])
        for c in names:
            if self.id != c.id:
                if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(" ", ""):
                    raise osv.except_osv(_('Error!'), _('Error: product category name must be unique'))
            else:
                pass


class product_uom(models.Model):
    _inherit = "product.uom"

    @api.constrains('name')
    def _check_duplicate_name(self):
        names = self.search([])
        for c in names:
            if self.id != c.id:
                if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(" ", ""):
                    raise osv.except_osv(_('Error!'), _('Error: unit of measure must be unique'))
            else:
                pass


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def unlink(self):
        for rec in self:
            purchase = self.env['purchase.order'].search([('partner_id', '=', rec.id)])
            if purchase:
                raise osv.except_osv(_('Error!'), _('Error: Existing Related Purchase Orders'))
            driver_daily = self.env['driver.daily.statement'].search([('diesel_pump2','=',rec.id)])
            if driver_daily:
                raise osv.except_osv(_('Error!'), _('Error: Existing Related Driver Daily Statements'))
            driver_daily_line = self.env['driver.daily.statement.line'].search([('from_id2','=',rec.id)])
            if driver_daily_line:
                raise osv.except_osv(_('Error!'), _('Error: Existing Related Driver Daily Statement Lines'))

            user = self.env['res.users'].search([('partner_id','=',rec.id)])
            if user:
                hr_employee_line = self.env['hr.employee'].search([('id', '=', user.employee_id.id)])
                if hr_employee_line:
                    hr_employee_line._cr.execute("DELETE FROM hr_employee WHERE id=%s", (user.employee_id.id,))
                user._cr.execute("DELETE FROM res_users WHERE id=%s", (user.id,))
            account_receivable_move_line = self.env['account.move.line'].search([('account_id','=',rec.property_account_receivable.id)])
            if account_receivable_move_line:
                raise osv.except_osv(_('Error!'), _('Error: Existing Related Move Lines'))

            account_payable_move_line = self.env['account.move.line'].search([('account_id','=',rec.property_account_payable.id)])
            if account_payable_move_line:
                raise osv.except_osv(_('Error!'), _('Error: Existing Related Move Lines'))

            account_receivable = self.env['account.account'].search([('id', '=', rec.property_account_receivable.id)])
            if account_receivable:
                print "account_receivable================", account_receivable
                self.env.cr.execute('DELETE FROM account_account WHERE id=%s', (account_receivable.id,))
            account_payable = self.env['account.account'].search([('id', '=', rec.property_account_payable.id)])
            if account_payable:
                self.env.cr.execute('DELETE FROM account_account WHERE id=%s', (account_payable.id,))
            models.Model.unlink(rec) 
        return

    @api.constrains('name')
    def _check_duplicate_name(self):
        names = self.search([])
        for c in names:
            if self.id != c.id:
                if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(" ", ""):
                    raise osv.except_osv(_('Error!'), _('Error: name must be unique'))
            else:
                pass

    # _sql_constraints = [
    #     ('name_uniq', 'unique (name)', 'The name must be unique !'),
    # ]

class account_account(models.Model):
    _inherit = 'account.account'

    @api.constrains('name')
    def _check_duplicate_name(self):
        names = self.search([])
        for c in names:
            if self.id != c.id:
                if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(" ", ""):
                    raise osv.except_osv(_('Error!'), _('Error: account name must be unique'))
            else:
                pass

    

class product_template(models.Model):
    _inherit = "product.template"

    @api.constrains('name')
    def _check_duplicate_name(self):
        names = self.search([])
        for c in names:
            # if list1 == list2 and self.name.lower() == c.name.lower() and self.id != c.id:
            if self.id != c.id:
                if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(" ", ""):
                    raise osv.except_osv(_('Error!'), _('Error: product name must be unique'))
            else:
                pass



# class StockWarehouse(models.Model):
#     _inherit = 'stock.warehouse'

#     @api.constrains('name')
#     def _check_duplicate_name(self):
#         names = self.search([])
#         for c in names:
#             if self.id != c.id:
#                 if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(" ", ""):
#                     raise osv.except_osv(_('Error!'), _('Error: warehouse name must be unique'))
#             else:
#                 pass


class StockLocation(models.Model):
    _inherit = 'stock.location'

    # @api.constrains('name')
    # def _check_duplicate_name(self):
    #     names = self.search([])
    #     for c in names:
    #         if self.id != c.id:
    #             if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(" ", ""):
    #                 raise osv.except_osv(_('Error!'), _('Error: location name must be unique'))
    #         else:
    #             pass


    related_account = fields.Many2one('account.account','Related Account')
    is_warehouse = fields.Boolean("Is a warehouse")


class project_attachment(models.Model):
    _inherit = 'project.attachment'
    
    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None: 
            context = {}
        line_num = 1    
    
        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context) 
            for line_rec in first_line_rec.activity_id.attachment_ids: 
                line_rec.line_no = line_num 
                line_num += 1 

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    activity_id = fields.Many2one('activity.activity', 'Activity')

class ActivityActivity(models.Model):
    _name = 'activity.activity'
    _order = 'date desc'
    
    name = fields.Char('Name')
    date = fields.Date('Date')
    attachment_ids = fields.One2many('project.attachment', 'activity_id', 'Attachments')
    remark = fields.Text('Remarks')
    state = fields.Selection([('draft', 'Draft'),
                                   ('progress', 'Progress'),
                                   ('completed', 'Completed'),
                                   ('cancel', 'Cancelled')
                                   ], 'Status', readonly=True, select=True, copy=False, default='draft')
                                   
    @api.multi
    def action_start(self):
        self.state = 'progress'
        
    @api.multi
    def action_done(self):
        self.state = 'completed'
        
    @api.multi
    def action_cancel(self):
        self.state = 'cancel'
        
    
                                   