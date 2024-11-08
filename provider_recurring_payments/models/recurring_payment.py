# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError


class RecurringPayment(models.Model):
    _name = 'recurring.payment'
    _description = 'Recurring Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # _rec_name = 'name'

    name = fields.Char('Name', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Partner", required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')
    amount = fields.Monetary(string="Total Amount", currency_field='currency_id')
    charging_amount = fields.Monetary(string="Charging Amount", currency_field='currency_id')
    journal_id = fields.Many2one('account.journal', 'Journal',
                                 related='template_id.journal_id', readonly=False, required=True)
    payment_type = fields.Selection([
        ('outbound', 'Send Money'),
        ('inbound', 'Receive Money'),
    ], string='Payment Type', required=True, default='inbound')
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('done', 'Done')], default='draft', string='Status')
    date_begin = fields.Date(string='Start Date', required=True)
    template_id = fields.Many2one('account.recurring.template', 'Recurring Template',
                                  domain=[('state', '=', 'done')],required=True)
    recurring_period = fields.Selection(related='template_id.recurring_period')
    
    # journal_state = fields.Selection(required=True, string='Generate Journal As',
    #                                  related='template_id.journal_state')

    description = fields.Text('Description')
    line_ids = fields.One2many('recurring.payment.line', 'recurring_payment_id', string='Recurring Lines')
    sale_id = fields.Many2one('sale.order', string="Sale Order" )
    invoice_id = fields.Many2one('account.move', string="Invoice")
    payment_token = fields.Many2one('payment.token', string='Payment Tokens', required=True)
    partner_related_ids = fields.Many2many('res.partner', string="Partner & Children", compute="_compute_partner_related_ids")
    @api.depends('partner_id')
    def _compute_partner_related_ids(self):
        for record in self:
            related_partners = record.partner_id.child_ids | record.partner_id | record.partner_id.parent_id
            record.partner_related_ids = related_partners

    def action_create_lines(self, amount,next_date):
        ids = self.env['recurring.payment.line']
        
        if self.invoice_id:
            vals = {
                # 'ref':str(self.invoice_id.name) +'/'+str(self.name)+'-'+ str(increment),
                'partner_id': self.partner_id.id,
                'amount': amount,
                'date': next_date,
                'recurring_payment_id': self.id,
                'invoice_id':self.invoice_id.id,
                'payment_token':self.payment_token.id,
                'journal_id': self.journal_id.id,
                'currency_id': self.currency_id.id,
                'state': 'draft'
            }
        elif self.sale_id:
            vals = {
            # 'ref':str(self.sale_id.name) +'/'+str(self.name)+'-'+ str(increment),
            'partner_id': self.partner_id.id,
            'amount': amount,
            'date': next_date,
            'recurring_payment_id': self.id,
            'journal_id': self.journal_id.id,
            'sale_id':self.sale_id.id,
            'payment_token':self.payment_token.id,
            'currency_id': self.currency_id.id,
            'state': 'draft'
        }
        else:
            vals = {
                    # 'ref':str(self.name)+'-'+ str(increment),
                    'partner_id': self.partner_id.id,
                    'amount': amount,
                    'date': next_date,
                    'recurring_payment_id': self.id,
                    'payment_token':self.payment_token.id,
                    'journal_id': self.journal_id.id,
                    'currency_id': self.currency_id.id,
                    'state': 'draft'
                }
        ids.create(vals)
        
    def load_invoice_lines(self):
        # validation
        if not self.journal_id:
            raise UserError(_("Please select journal and try again."))
        if not self.recurring_period:
            raise UserError(_("Please select recurring period and try again."))
        
        if not self.amount:
            raise UserError(_("Please add amount and try again."))
        if not self.charging_amount:
            raise UserError(_("Please add charging amount and try again."))
        # delete present lines
        lines = self.env['recurring.payment.line'].search([('recurring_payment_id', '=', self.id)])
        if lines:
            lines.unlink()
        
        next_date = self.date_begin
        
        total_amount = self.amount
        amount = 0
        # increment = 1
        if self.recurring_period == 'days':
            while amount <= total_amount:
                remaining_amount = total_amount - amount
                if remaining_amount < self.charging_amount:
                    # self.action_create_lines(remaining_amount, next_date, increment)
                    self.action_create_lines(remaining_amount, next_date)
                    break
                else:
                    # self.action_create_lines(self.charging_amount, next_date, increment)

                    self.action_create_lines(self.charging_amount, next_date)
                
                next_date += relativedelta(days=1)
                amount += self.charging_amount
                # increment += 1
            # update contract end date
        elif self.recurring_period == 'weeks':
            while amount <= total_amount:
                remaining_amount = total_amount - amount
                if remaining_amount < self.charging_amount:
                    self.action_create_lines(remaining_amount, next_date)
                    break
                else:
                    self.action_create_lines(self.charging_amount, next_date)
                next_date += relativedelta(weeks=1)
                amount += self.charging_amount
                # increment += 1
        elif self.recurring_period == 'months':
            while amount <= total_amount:
                remaining_amount = total_amount - amount
                if remaining_amount < self.charging_amount:
                    self.action_create_lines(remaining_amount, next_date)
                    break
                else:
                    self.action_create_lines(self.charging_amount, next_date)
                next_date += relativedelta(months=1) 
                amount += self.charging_amount
                # increment += 1
        elif self.recurring_period == 'quarterly':
            while amount <= total_amount:
                remaining_amount = total_amount - amount
                if remaining_amount < self.charging_amount:
                    self.action_create_lines(remaining_amount, next_date)
                    break
                else:
                    self.action_create_lines(self.charging_amount, next_date)
                next_date += relativedelta(months=3)
                amount += self.charging_amount
                # increment += 1
        elif self.recurring_period == 'bi_yearly':
            while amount <= total_amount:
                remaining_amount = total_amount - amount
                if remaining_amount < self.charging_amount:
                    self.action_create_lines(remaining_amount, next_date)
                    break
                else:
                    self.action_create_lines(self.charging_amount, next_date)
                next_date += relativedelta(months=6)
                amount += self.charging_amount
                # increment += 1
        elif self.recurring_period == 'years':
            while amount <= total_amount:
                remaining_amount = total_amount - amount
                if remaining_amount < self.charging_amount:
                    self.action_create_lines(remaining_amount, next_date)
                    break
                else:
                    self.action_create_lines(self.charging_amount, next_date)
                next_date += relativedelta(years=1)
                amount += self.charging_amount
                # increment += 1
    def action_done(self):
        self.load_invoice_lines()
        self.state = 'done'

    def action_draft(self):
        if self.line_ids.filtered(lambda t: t.state == 'done'):
            raise ValidationError(_('You cannot Set to Draft as one of the line is already in done state'))
        else:
            for line in self.line_ids:
                line.unlink()
            self.state = 'draft'

    def action_generate_payment(self):
        line_ids = self.env['recurring.payment.line'].search([('date', '<=', date.today()),
                                                              ('state', '!=', 'done'),
                                                              ('skip_payment','!=', True)])
        for line in line_ids:
            line.action_send_payment_request()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code(
                    'recurring.payment') or _('New')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('recurring.payment') or _('New')
        return super(RecurringPayment, self).create(vals)

    @api.constrains('amount')
    def _check_amount(self):
        if self.amount <= 0:
            raise ValidationError(_('Total Amount Must Be Non-Zero Positive Number'))
        if self.charging_amount <= 0 :
            raise ValidationError(_('Charge Amount Must Be Non-Zero Positive Number'))
        if self.charging_amount > self.amount:
            raise ValidationError(_('Chage Amount Must Be Non-Zero Positive Number or Must less then Total Amount'))
    def unlink(self):
        for rec in self:
            if rec.state == 'done':
                raise ValidationError(_('Cannot delete done records !'))
        return super(RecurringPayment, self).unlink()


class RecurringPaymentLine(models.Model):
    _name = 'recurring.payment.line'
    _description = 'Recurring Payment Line'

    recurring_payment_id = fields.Many2one('recurring.payment', string="Recurring Payment")
    partner_id = fields.Many2one('res.partner', 'Partner', required=True)
    amount = fields.Monetary('Amount', required=True, default=0.0)
    date = fields.Date('Date', default=date.today(), tracking=True)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')
    payment_id = fields.Many2one('account.payment', string='Payment')
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('done', 'Done')], default='draft', string='Status')
    payment_token = fields.Many2one('payment.token', string='Payment Tokens', required=True)

    invoice_id =  fields.Many2one('account.move',string="Invoice")
    sale_id = fields.Many2one('sale.order', string="Sale Order" )
    skip_payment = fields.Boolean(string="Skip Payment")

    
    ref = fields.Char(string="Reference")
    # def action_create_payment(self):
    #     vals = {
    #         'payment_type': self.recurring_payment_id.payment_type,
    #         'amount': self.amount,
    #         'currency_id': self.currency_id.id,
    #         'journal_id': self.journal_id.id,
    #         'company_id': self.company_id.id,
    #         'date': self.date,
    #         'ref': self.recurring_payment_id.name,
    #         'partner_id': self.partner_id.id,
    #     }
    #     payment = self.env['account.payment'].create(vals)
    #     if payment:
    #         # if self.recurring_payment_id.journal_state == 'posted':
    #         #     payment.action_post()
    #         self.write({'state': 'done', 'payment_id': payment.id})
    
    def write(self, vals):
        # Log or track the changes
        
        recurring_payment = self.env['recurring.payment'].search([('id', '=', self.recurring_payment_id.id)])
        row = 1
        if recurring_payment:
            references = self.search([('recurring_payment_id','=',recurring_payment.id)], order='id asc').ids
            for ref in references:
                if ref == self.id:
                    break  # Stop when the current record is found
                row += 1

        if 'date' in vals:
            
            data_change = " \u2022 <b>" + str('Date') + '</b>:' + \
                            '<b>' + str(self.date) + '</b>' + '→' + \
                            '<span style="color:blue">' + '<b>' + str(vals['date']) + '</b>' + '</span>'  +\
                                '(' + '<b>' + 'In Row'+' '+str(row) + '</b>' + ')' + "<br/>"            
            self.recurring_payment_id.message_post(body=data_change)
        if 'skip_payment' in vals:
            if vals['skip_payment'] == True:
                toggle_change =  " \u2022 <b>" + str('Skip Payment') + '</b>:' + \
                            '<b>' + str(self.skip_payment) + '</b>' + '→' + \
                            '<span style="color:blue">' + '<b>' + str(vals['skip_payment']) + '</b>' + '</span>'  +\
                                 '(' + '<b>' + 'In Row'+' '+str(row) + '</b>' + ')' +"<br/>"
            else:
                toggle_change =  " \u2022 <b>" + str('Skip Payment') + '</b>:' + \
                            '<b>' + str(self.skip_payment) + '</b>' + '→' + \
                            '<span style="color:red">' + '<b>' + str(vals['skip_payment']) + '</b>' + '</span>'  +\
                                 '(' + '<b>' + 'In Row'+' '+str(row) + '</b>' + ')' +"<br/>"
            # str(vals['skip_payment']) +'->'+ str(self.skip_payment)
            self.recurring_payment_id.message_post(body=toggle_change)
        
        return super(RecurringPaymentLine, self).write(vals)
    # def _log_session_tracking(self):
    #     template_id = 
    
    
    def _get_next_reference_number(self):
        """Helper method to get the next increment number for the reference"""
        recurring_payment = self.env['recurring.payment'].search([('id', '=', self.recurring_payment_id.id)])
        if recurring_payment:
            references = self.search([('recurring_payment_id','=',recurring_payment.id),('state', '=', 'done')])
        
            max_number = 0  # Initialize the max_number

            for record in references:
                # Get the last part of the reference
                if record.ref:
                    try:
                        # Split by '-' and convert to integer
                        last_part = record.ref.split('-')[-1]
                        last_number = int(last_part)
                        max_number = max(max_number, last_number)  # Update max_number if necessary
                    except ValueError:
                        print(f"Warning: Unable to convert '{last_part}' to an integer")

            print("Maximum reference number found: ", max_number)
            
            return max_number + 1 
    
    def action_send_payment_request(self):
        if not self.skip_payment:
            
            if self.invoice_id:
                reference = self.invoice_id.name +'/'+self.recurring_payment_id.name +'-'+ str(self._get_next_reference_number())
                self.write({'ref':reference})
                transaction = self._do_payment(self.payment_token, self.invoice_id, self.amount)
                self.invoice_id.write({'payment_reference': transaction.reference, 'ref': transaction.reference})
            elif self.sale_id:
                reference = self.sale_id.name +'/'+self.recurring_payment_id.name +'-'+ str(self._get_next_reference_number())
                self.write({'ref':reference})
                self._do_payment(self.payment_token, self.sale_id, self.amount)
            else:
                reference = self.recurring_payment_id.name +'-'+ str(self._get_next_reference_number())
                self.write({'ref':reference})
                self._do_payment(self.payment_token,  self.amount, invoice_so=None)
       
    
    def _do_payment(self, payment_token, amount, invoice_so):
        tx_obj = self.env['payment.transaction']
        values = []
        
        if self.invoice_id:
            sale_ids = invoice_so.line_ids.sale_line_ids.mapped('order_id')

            values.append({
                'provider_id': payment_token.provider_id.id,
                'sale_order_ids':  [(6, 0, sale_ids.ids)] if sale_ids else False,
                'reference': self.ref,
                'amount': amount,
                'currency_id': invoice_so.currency_id.id,
                'partner_id': payment_token.partner_id.id,
                'token_id': payment_token.id,
                'tokenize': False,
                'operation': 'online_token',
                'invoice_ids': [(6, 0, [invoice_so.id])],
                'callback_model_id': self.env['ir.model']._get_id(payment_token.partner_id._name),
                'callback_res_id':  payment_token.partner_id.id,
                # 'callback_method': 'reconcile_pending_transaction'
            })
        elif self.sale_id:
            values.append({
            'provider_id': payment_token.provider_id.id,
            'sale_order_ids':  [(6, 0, [invoice_so.id])],
            'reference': self.ref,
            'amount': amount,
            'currency_id': invoice_so.currency_id.id,
            'partner_id': payment_token.partner_id.id,
            'token_id': payment_token.id,
            'tokenize': False,
            'operation': 'online_token',
            'callback_model_id': self.env['ir.model']._get_id(payment_token.partner_id._name),
            'callback_res_id':  payment_token.partner_id.id,
            # 'callback_method': 'reconcile_pending_transaction'
            })
        else:
            values.append({
            'provider_id': payment_token.provider_id.id,
            'sale_order_ids':  False,
            'reference': self.ref,
            'amount': amount,
            'currency_id': self.currency_id.id,
            'partner_id': payment_token.partner_id.id,
            'token_id': payment_token.id,
            'tokenize': False,
            'operation': 'online_token',
            'callback_model_id': self.env['ir.model']._get_id(payment_token.partner_id._name),
            'callback_res_id':  payment_token.partner_id.id,
            # 'callback_method': 'reconcile_pending_transaction'
            })
        
        transactions = tx_obj.create(values)
        
        for tx in transactions:
            tx._send_payment_request()
            tx._get_processing_values()
            tx._reconcile_after_done()
        payment = self.env['account.payment'].search([('payment_transaction_id','=',self.ref)])
        self.write({'state': 'done', 'payment_id': payment.id})
        return transactions