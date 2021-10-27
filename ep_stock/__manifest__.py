{
    'name': 'EP Stock Management',
    'version': '14.0.1.0.0',
    'category': 'Inventory',
    'summary': 'EP Stock Management',
    'author': "Mohamed Saber, SIEMENS S.A.E",
    'website': 'http://www.siemens.com.eg',
    'license': 'AGPL-3',
    'depends': [
        'base','mail','product', 'stock'
    ],
    'data': [
        'security/stock_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/product_template_view.xml',
        'views/res_partner_view.xml',
        'views/stock_picking_views.xml',
        'views/users_view.xml',
        'views/purchase_inquiry_view.xml',
    ],
    'installable': True,
}
