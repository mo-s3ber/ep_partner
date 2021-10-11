{
    'name': 'EP Stock Management',
    'version': '14.0.1.0.0',
    'category': 'Inventory',
    'summary': 'EP Stock Management',
    'author': "Mohamed Saber, SIEMENS S.A.E",
    'website': 'http://www.siemens.com.eg',
    'license': 'AGPL-3',
    'depends': [
        'mail', 'stock',
    ],
    'data': [
        # 'security/ir.model.access.csv',
        'security/stock_security.xml',
        'views/product_template_view.xml',
        'views/res_partner_view.xml',
        'views/stock_picking_views.xml',
        'views/users_view.xml',
    ],
    'installable': True,
}
