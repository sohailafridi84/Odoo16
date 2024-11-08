
{
    'name': 'Provider Recurring Payment',
    'author': 'Sohail Afridi',
    'category': 'Accounting',
    'version': '1.0.0',
    'description': """Odoo 16 Recurring Payment, Recurring Payment In Odoo, Odoo 16 Accounting""",
    'summary': 'Use recurring payments to handle periodically repeated payments',
    'sequence': 11,
    'depends': ['account','sale'],
    'license': 'LGPL-3',
    'data': [
        'data/sequence.xml',
        'data/recurring_cron.xml',
        'security/ir.model.access.csv',
        'views/recurring_template_view.xml',
        'views/recurring_payment_view.xml'
    ],
    'images': ['static/description/banner.png'],
}
