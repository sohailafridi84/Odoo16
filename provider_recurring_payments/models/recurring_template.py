# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import models, fields, api


class AccountRecurringTemplate(models.Model):
    _name = 'account.recurring.template'
    _description = 'Recurring Template'
    _rec_name = 'name'

    name = fields.Char('Name', required=True)
    # account_id = fields.Many2one('account.account', 'Account', required=True)
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    recurring_period = fields.Selection(selection=[('days', 'Days'),
                                                   ('weeks', 'Weeks'),
                                                   ('months', 'Months'),
                                                   ('quarterly','Quarter'),
                                                   ('bi_yearly','Bi-Yearly'),
                                                   ('years', 'Years')], store=True, required=True)
    
    description = fields.Text('Description')
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('done', 'Done')], default='draft', string='Status')
    # journal_state = fields.Selection(selection=[('draft', 'Un Posted'),
    #                                             ('posted', 'Posted')],
    #                                  required=True, default='draft', string='Generate Journal As')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id)
    
    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_done(self):
        for rec in self:
            rec.state = 'done'


