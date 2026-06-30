"""
Jewelitics Chatbot — Simple command-based assistant.
Responds to keywords/commands using real database queries.
No external API required.
"""
from models import db
from models.product import Product, Category
from models.order import Order, OrderItem
from models.supplier import Supplier
from models.user import User
from models.notification import SalesSummary
from sqlalchemy import func
from datetime import datetime, timedelta


def chat_response(message, user):
    """Process user message and return a data-driven reply."""
    msg = message.lower().strip()
    role = user.role

    # ─── HELP ───
    if msg in ('help', '/help', 'commands', 'menu'):
        return _help_reply(role)

    # ─── GREETINGS ───
    if msg in ('hi', 'hello', 'hey', 'hii', 'hiii', 'good morning', 'good evening', 'good afternoon'):
        return {'reply': f"Hello {user.full_name}! 💎 Welcome to Jewelitics.\n\nType **help** to see what I can do for you!"}

    # ─── PRODUCT QUERIES ───
    if any(kw in msg for kw in ['product', 'catalog', 'all product', 'show product', 'list product', 'inventory list']):
        return _products_reply()

    if any(kw in msg for kw in ['categor', 'types', 'collections']):
        return _categories_reply()

    if any(kw in msg for kw in ['gold', 'silver', 'platinum', 'diamond']):
        material = None
        if 'gold' in msg:
            material = 'Gold'
        elif 'silver' in msg:
            material = 'Silver'
        elif 'platinum' in msg:
            material = 'Platinum'
        elif 'diamond' in msg:
            material = 'Gold'  # Diamond jewelry is usually gold
        return _material_products_reply(material)

    if any(kw in msg for kw in ['cheap', 'budget', 'affordable', 'lowest price', 'low price']):
        return _cheapest_products_reply()

    if any(kw in msg for kw in ['expensive', 'premium', 'luxury', 'high end', 'costly']):
        return _expensive_products_reply()

    if any(kw in msg for kw in ['search', 'find', 'look for']):
        # Extract search term
        for prefix in ['search', 'find', 'look for']:
            if prefix in msg:
                term = msg.split(prefix, 1)[1].strip()
                if term:
                    return _search_products_reply(term)
        return {'reply': "🔍 What would you like to search for? Try: **search ring** or **find necklace**"}

    if any(kw in msg for kw in ['ring', 'necklace', 'pendant', 'bangle', 'earring', 'chain',
                                  'bracelet', 'mangalsutra', 'anklet', 'choker', 'coin']):
        return _search_products_reply(msg)

    # ─── STOCK QUERIES (staff/admin only) ───
    if any(kw in msg for kw in ['low stock', 'stock alert', 'restock', 'running low']):
        if role == 'customer':
            return {'reply': "I can help you with product availability! Which product are you interested in?"}
        return _low_stock_reply()

    if any(kw in msg for kw in ['out of stock', 'no stock', 'unavailable']):
        if role == 'customer':
            return {'reply': "Let me check availability for you. Which product are you looking for?"}
        return _out_of_stock_reply()

    if any(kw in msg for kw in ['stock', 'inventory']) and role != 'customer':
        return _inventory_summary_reply()

    # ─── SALES QUERIES (staff/admin only) ───
    if any(kw in msg for kw in ['today sale', 'today\'s sale', 'today revenue', 'daily sale']):
        if role == 'customer':
            return _no_access_reply()
        return _today_sales_reply()

    if any(kw in msg for kw in ['month sale', 'monthly sale', 'this month', 'month revenue']):
        if role == 'customer':
            return _no_access_reply()
        return _monthly_sales_reply()

    if any(kw in msg for kw in ['total sale', 'all time', 'overall sale', 'all sale']):
        if role == 'customer':
            return _no_access_reply()
        return _all_time_sales_reply()

    if any(kw in msg for kw in ['top sell', 'best sell', 'popular', 'most sold', 'top product']):
        if role == 'customer':
            return _no_access_reply()
        return _top_selling_reply()

    if any(kw in msg for kw in ['sale', 'revenue', 'earning']):
        if role == 'customer':
            return _no_access_reply()
        return _today_sales_reply()

    # ─── ORDER QUERIES ───
    if any(kw in msg for kw in ['my order', 'order status', 'my purchase']):
        if role == 'customer':
            return _customer_orders_reply(user)
        return _orders_summary_reply()

    if any(kw in msg for kw in ['pending order', 'pending']):
        if role == 'customer':
            return _customer_orders_reply(user)
        return _pending_orders_reply()

    if any(kw in msg for kw in ['order', 'orders']):
        if role == 'customer':
            return _customer_orders_reply(user)
        return _orders_summary_reply()

    # ─── CUSTOMER/USER QUERIES (staff/admin only) ───
    if any(kw in msg for kw in ['customer', 'how many customer', 'user count', 'total user']):
        if role == 'customer':
            return _no_access_reply()
        return _customers_reply()

    # ─── SUPPLIER QUERIES (admin only) ───
    if any(kw in msg for kw in ['supplier', 'vendor', 'purchase order']):
        if role != 'admin':
            return _no_access_reply()
        return _suppliers_reply()

    # ─── PROFIT QUERIES (admin only) ───
    if any(kw in msg for kw in ['profit', 'margin', 'earning']):
        if role != 'admin':
            return _no_access_reply()
        return _profit_reply()

    # ─── SUMMARY / OVERVIEW ───
    if any(kw in msg for kw in ['summary', 'overview', 'dashboard', 'report', 'status']):
        if role == 'customer':
            return _customer_summary_reply(user)
        return _business_summary_reply(role)

    # ─── THANK YOU ───
    if any(kw in msg for kw in ['thank', 'thanks', 'thx', 'ty']):
        return {'reply': "You're welcome! 😊 Happy to help. Type **help** if you need anything else! 💎"}

    # ─── BYE ───
    if any(kw in msg for kw in ['bye', 'goodbye', 'see you', 'exit', 'quit']):
        return {'reply': f"Goodbye {user.full_name}! 👋 Have a wonderful day! 💎"}

    # ─── DEFAULT ───
    return {'reply': f"I didn't quite understand that. 🤔\n\nTry one of these:\n"
                     f"• **help** — see all commands\n"
                     f"• **products** — view catalog\n"
                     f"• **categories** — browse by type\n"
                     f"• **search ring** — find specific items\n"
                     + ("• **low stock** — stock alerts\n• **sales** — sales data\n" if role != 'customer' else '')
                     + "\nOr just type a product name like **necklace** or **gold**!"}


# ═══════════════════════════════════════════
# REPLY BUILDERS
# ═══════════════════════════════════════════

def _help_reply(role):
    lines = ["💎 **Jewelitics Commands:**\n"]
    lines.append("**Product Commands:**")
    lines.append("• **products** — View all products")
    lines.append("• **categories** — View all categories")
    lines.append("• **search [name]** — Search for products")
    lines.append("• **gold / silver / platinum** — Filter by material")
    lines.append("• **budget** — Cheapest items")
    lines.append("• **premium** — Most expensive items\n")

    if role in ('staff', 'admin'):
        lines.append("**Inventory & Sales:**")
        lines.append("• **stock** — Inventory summary")
        lines.append("• **low stock** — Items running low")
        lines.append("• **out of stock** — Unavailable items")
        lines.append("• **today sales** — Today's revenue")
        lines.append("• **monthly sales** — This month's data")
        lines.append("• **top selling** — Best sellers")
        lines.append("• **orders** — Order summary")
        lines.append("• **pending** — Pending orders")
        lines.append("• **customers** — Customer count\n")

    if role == 'admin':
        lines.append("**Admin Only:**")
        lines.append("• **suppliers** — Supplier list")
        lines.append("• **profit** — Profit analysis")
        lines.append("• **summary** — Full business overview\n")

    if role == 'customer':
        lines.append("**Your Account:**")
        lines.append("• **my orders** — Your order history")
        lines.append("• **summary** — Your account overview\n")

    return {'reply': "\n".join(lines)}


def _products_reply():
    products = Product.query.order_by(Product.selling_price.desc()).all()
    if not products:
        return {'reply': "📦 No products in the catalog yet."}

    lines = [f"🛍️ **Product Catalog** ({len(products)} items)\n"]
    for p in products[:15]:  # Show top 15
        status = "✅" if p.quantity > p.min_stock else ("⚠️" if p.quantity > 0 else "❌")
        lines.append(f"{status} **{p.name}** — ₹{p.selling_price:,.0f} | {p.material} {p.purity} | {p.weight}g")

    if len(products) > 15:
        lines.append(f"\n... and {len(products) - 15} more products.")
    return {'reply': "\n".join(lines)}


def _categories_reply():
    cats = Category.query.all()
    if not cats:
        return {'reply': "📂 No categories found."}

    lines = [f"📂 **Categories** ({len(cats)})\n"]
    for c in cats:
        count = len(c.products) if c.products else 0
        lines.append(f"• **{c.name}** — {count} products")
    return {'reply': "\n".join(lines)}


def _material_products_reply(material):
    products = Product.query.filter_by(material=material).order_by(Product.selling_price.desc()).all()
    if not products:
        return {'reply': f"No {material} products found."}

    lines = [f"🥇 **{material} Products** ({len(products)} items)\n"]
    for p in products:
        lines.append(f"• **{p.name}** — ₹{p.selling_price:,.0f} | {p.purity} | {p.weight}g")
    return {'reply': "\n".join(lines)}


def _cheapest_products_reply():
    products = Product.query.order_by(Product.selling_price.asc()).limit(5).all()
    lines = ["💰 **Most Affordable Items:**\n"]
    for i, p in enumerate(products, 1):
        lines.append(f"{i}. **{p.name}** — ₹{p.selling_price:,.0f}")
    return {'reply': "\n".join(lines)}


def _expensive_products_reply():
    products = Product.query.order_by(Product.selling_price.desc()).limit(5).all()
    lines = ["👑 **Premium Collection:**\n"]
    for i, p in enumerate(products, 1):
        lines.append(f"{i}. **{p.name}** — ₹{p.selling_price:,.0f}")
    return {'reply': "\n".join(lines)}


def _search_products_reply(term):
    products = Product.query.filter(Product.name.ilike(f'%{term}%')).all()
    if not products:
        return {'reply': f"🔍 No products found for **\"{term}\"**. Try a different keyword!"}

    lines = [f"🔍 **Search results for \"{term}\"** ({len(products)} found)\n"]
    for p in products:
        lines.append(f"• **{p.name}** — ₹{p.selling_price:,.0f} | {p.material} {p.purity} | Stock: {p.quantity}")
    return {'reply': "\n".join(lines)}


def _low_stock_reply():
    low = Product.query.filter(Product.quantity <= Product.min_stock, Product.quantity > 0).all()
    if not low:
        return {'reply': "✅ All products are well stocked! No alerts."}

    lines = [f"⚠️ **Low Stock Alert** ({len(low)} items)\n"]
    for p in low:
        lines.append(f"⚠️ **{p.name}** — {p.quantity} left (min: {p.min_stock})")
    return {'reply': "\n".join(lines)}


def _out_of_stock_reply():
    out = Product.query.filter_by(quantity=0).all()
    if not out:
        return {'reply': "✅ No products are out of stock!"}

    lines = [f"❌ **Out of Stock** ({len(out)} items)\n"]
    for p in out:
        lines.append(f"❌ **{p.name}** — SKU: {p.sku}")
    return {'reply': "\n".join(lines)}


def _inventory_summary_reply():
    total_products = Product.query.count()
    total_qty = db.session.query(func.sum(Product.quantity)).scalar() or 0
    total_value = db.session.query(func.sum(Product.selling_price * Product.quantity)).scalar() or 0
    low = Product.query.filter(Product.quantity <= Product.min_stock, Product.quantity > 0).count()
    out = Product.query.filter_by(quantity=0).count()

    return {'reply': f"📦 **Inventory Summary**\n\n"
                     f"• Total Products: **{total_products}**\n"
                     f"• Total Items in Stock: **{total_qty}**\n"
                     f"• Total Stock Value: **₹{total_value:,.0f}**\n"
                     f"• Low Stock Items: **{low}** ⚠️\n"
                     f"• Out of Stock: **{out}** ❌"}


def _today_sales_reply():
    today = datetime.utcnow().date()
    s = SalesSummary.query.filter_by(sale_date=today).first()
    if not s:
        return {'reply': f"📊 **Today ({today.strftime('%b %d')}):** No sales recorded yet."}

    return {'reply': f"📊 **Today's Sales** ({today.strftime('%b %d, %Y')})\n\n"
                     f"• Revenue: **₹{s.total_sales:,.0f}**\n"
                     f"• Profit: **₹{s.total_profit:,.0f}**\n"
                     f"• Orders: **{s.total_orders}**"}


def _monthly_sales_reply():
    today = datetime.utcnow().date()
    month_start = today.replace(day=1)
    result = db.session.query(
        func.sum(SalesSummary.total_sales),
        func.sum(SalesSummary.total_profit),
        func.sum(SalesSummary.total_orders)
    ).filter(SalesSummary.sale_date >= month_start).first()

    rev = result[0] or 0
    profit = result[1] or 0
    orders = result[2] or 0

    return {'reply': f"📈 **{today.strftime('%B %Y')} Sales**\n\n"
                     f"• Revenue: **₹{rev:,.0f}**\n"
                     f"• Profit: **₹{profit:,.0f}**\n"
                     f"• Orders: **{orders}**"}


def _all_time_sales_reply():
    result = db.session.query(
        func.sum(SalesSummary.total_sales),
        func.sum(SalesSummary.total_profit),
        func.sum(SalesSummary.total_orders)
    ).first()

    return {'reply': f"📊 **All-Time Sales**\n\n"
                     f"• Total Revenue: **₹{(result[0] or 0):,.0f}**\n"
                     f"• Total Profit: **₹{(result[1] or 0):,.0f}**\n"
                     f"• Total Orders: **{result[2] or 0}**"}


def _top_selling_reply():
    top = db.session.query(
        Product.name, func.sum(OrderItem.quantity).label('qty')
    ).join(OrderItem, Product.id == OrderItem.product_id
    ).group_by(Product.name).order_by(func.sum(OrderItem.quantity).desc()).limit(5).all()

    if not top:
        return {'reply': "🏆 No sales data yet to determine top sellers."}

    lines = ["🏆 **Top Selling Products**\n"]
    for i, (name, qty) in enumerate(top, 1):
        medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i - 1]
        lines.append(f"{medal} **{name}** — {qty} sold")
    return {'reply': "\n".join(lines)}


def _orders_summary_reply():
    total = Order.query.count()
    if total == 0:
        return {'reply': "📋 No orders yet."}

    pending = Order.query.filter_by(status='pending').count()
    processing = Order.query.filter(Order.status.in_(['accepted', 'processing', 'packed'])).count()
    shipped = Order.query.filter_by(status='shipped').count()
    delivered = Order.query.filter_by(status='delivered').count()
    cancelled = Order.query.filter_by(status='cancelled').count()

    lines = [f"📋 **Orders Summary** ({total} total)\n"]
    lines.append(f"• ⏳ Pending: **{pending}**")
    lines.append(f"• 🔄 Processing: **{processing}**")
    lines.append(f"• 🚚 Shipped: **{shipped}**")
    lines.append(f"• ✅ Delivered: **{delivered}**")
    lines.append(f"• ❌ Cancelled: **{cancelled}**")

    recent = Order.query.order_by(Order.created_at.desc()).limit(3).all()
    if recent:
        lines.append("\n**Recent Orders:**")
        for o in recent:
            lines.append(f"• {o.order_number} — ₹{o.total_amount:,.0f} — {o.status.capitalize()}")

    return {'reply': "\n".join(lines)}


def _pending_orders_reply():
    pending = Order.query.filter_by(status='pending').order_by(Order.created_at.desc()).all()
    if not pending:
        return {'reply': "✅ No pending orders! All caught up."}

    lines = [f"⏳ **Pending Orders** ({len(pending)})\n"]
    for o in pending[:10]:
        lines.append(f"• **{o.order_number}** — ₹{o.total_amount:,.0f} — {o.created_at.strftime('%b %d')}")
    return {'reply': "\n".join(lines)}


def _customer_orders_reply(user):
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    if not orders:
        return {'reply': "📋 You haven't placed any orders yet. Visit our **Shop** to browse products! 🛍️"}

    lines = [f"📋 **Your Orders** ({len(orders)})\n"]
    for o in orders[:10]:
        status_icon = {'pending': '⏳', 'accepted': '✅', 'processing': '🔄', 'packed': '📦',
                       'shipped': '🚚', 'delivered': '✅', 'cancelled': '❌'}.get(o.status, '📋')
        lines.append(f"{status_icon} **{o.order_number}** — ₹{o.total_amount:,.0f} — {o.status.capitalize()} — {o.created_at.strftime('%b %d')}")
    return {'reply': "\n".join(lines)}


def _customers_reply():
    total = User.query.filter_by(role='customer').count()
    recent = User.query.filter_by(role='customer').order_by(User.created_at.desc()).limit(5).all()

    lines = [f"👥 **Customers: {total}**\n"]
    if recent:
        lines.append("**Recent Customers:**")
        for c in recent:
            lines.append(f"• **{c.full_name}** — {c.email} — Joined {c.created_at.strftime('%b %d')}")
    return {'reply': "\n".join(lines)}


def _suppliers_reply():
    suppliers = Supplier.query.all()
    if not suppliers:
        return {'reply': "🚚 No suppliers added yet."}

    lines = [f"🚚 **Suppliers** ({len(suppliers)})\n"]
    for s in suppliers:
        lines.append(f"• **{s.name}** — {s.phone} — {s.city}, {s.state}")
    return {'reply': "\n".join(lines)}


def _profit_reply():
    total_value = db.session.query(func.sum(Product.selling_price * Product.quantity)).scalar() or 0
    total_cost = db.session.query(func.sum(Product.purchase_price * Product.quantity)).scalar() or 0
    potential_profit = total_value - total_cost

    result = db.session.query(
        func.sum(SalesSummary.total_sales),
        func.sum(SalesSummary.total_profit)
    ).first()

    return {'reply': f"💵 **Profit Analysis**\n\n"
                     f"**Stock Potential:**\n"
                     f"• Stock Value (Selling): **₹{total_value:,.0f}**\n"
                     f"• Stock Cost: **₹{total_cost:,.0f}**\n"
                     f"• Potential Profit: **₹{potential_profit:,.0f}**\n\n"
                     f"**Realized Sales:**\n"
                     f"• Total Revenue: **₹{(result[0] or 0):,.0f}**\n"
                     f"• Total Profit: **₹{(result[1] or 0):,.0f}**"}


def _customer_summary_reply(user):
    order_count = Order.query.filter_by(user_id=user.id).count()
    total_spent = db.session.query(func.sum(Order.total_amount)).filter_by(user_id=user.id).scalar() or 0
    product_count = Product.query.count()

    return {'reply': f"📊 **Your Account Summary**\n\n"
                     f"• Name: **{user.full_name}**\n"
                     f"• Email: **{user.email}**\n"
                     f"• Orders Placed: **{order_count}**\n"
                     f"• Total Spent: **₹{total_spent:,.0f}**\n"
                     f"• Products Available: **{product_count}** 🛍️"}


def _business_summary_reply(role):
    total_products = Product.query.count()
    total_qty = db.session.query(func.sum(Product.quantity)).scalar() or 0
    stock_value = db.session.query(func.sum(Product.selling_price * Product.quantity)).scalar() or 0
    low_stock = Product.query.filter(Product.quantity <= Product.min_stock, Product.quantity > 0).count()
    total_orders = Order.query.count()
    pending = Order.query.filter_by(status='pending').count()
    customers = User.query.filter_by(role='customer').count()

    today = datetime.utcnow().date()
    today_sales = SalesSummary.query.filter_by(sale_date=today).first()
    today_rev = today_sales.total_sales if today_sales else 0

    lines = ["📊 **Business Overview**\n"]
    lines.append(f"**Inventory:**")
    lines.append(f"• Products: **{total_products}** | Items: **{total_qty}**")
    lines.append(f"• Stock Value: **₹{stock_value:,.0f}**")
    lines.append(f"• Low Stock Alerts: **{low_stock}** ⚠️\n")
    lines.append(f"**Sales:**")
    lines.append(f"• Today's Revenue: **₹{today_rev:,.0f}**\n")
    lines.append(f"**Orders:**")
    lines.append(f"• Total: **{total_orders}** | Pending: **{pending}** ⏳\n")
    lines.append(f"**Users:**")
    lines.append(f"• Customers: **{customers}**")

    if role == 'admin':
        suppliers = Supplier.query.count()
        lines.append(f"• Suppliers: **{suppliers}**")

    return {'reply': "\n".join(lines)}


def _no_access_reply():
    return {'reply': "🔒 Sorry, you don't have access to that information.\n\nTry asking about **products**, **categories**, or **your orders**!"}
