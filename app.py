import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'services.db')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'change_this_secret_in_prod'  # change for production

db = SQLAlchemy(app)

# ---------- Models ----------
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    def __repr__(self):
        return f"<Category {self.name}>"

class Provider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=True)
    contact = db.Column(db.String(80), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    price_range = db.Column(db.String(80), nullable=True)
    rating = db.Column(db.Float, nullable=True)
    approved = db.Column(db.Boolean, default=False)
    transaction_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Provider {self.name} - {self.category}>"

# ---------- Seed categories ----------
DEFAULT_CATEGORIES = [
    'Plumber', 'Electrician', 'Tutor', 'Event Planner', 'Painter',
    'Carpenter', 'Cleaner', 'Gardener', 'AC Repair', 'Mechanic'
]

def seed_categories():
    if Category.query.count() == 0:
        for c in DEFAULT_CATEGORIES:
            db.session.add(Category(name=c))
        db.session.commit()
        print("Seeded categories.")

# ---------- EasyPaisa ----------
EASYPAYSA_NUMBER = "03115939025"

# ---------- Context processor ----------
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# ---------- Routes ----------
@app.route('/')
def index():
    categories = Category.query.order_by(Category.name).all()
    latest_providers = Provider.query.filter_by(approved=True).order_by(Provider.created_at.desc()).limit(6).all()
    return render_template('index.html', categories=categories, latest_providers=latest_providers)

@app.route('/search')
def search():
    category = request.args.get('category', '').strip()
    city = request.args.get('city', '').strip()
    q = Provider.query.filter(Provider.approved == True)

    if category:
        q = q.filter(Provider.category == category)
    if city:
        q = q.filter(Provider.city.ilike(f"%{city}%"))

    providers = q.order_by(Provider.created_at.desc()).all()
    return render_template('search_results.html', providers=providers, category=category, city=city)

@app.route('/provider/register', methods=['GET', 'POST'])
def provider_register():
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        description = request.form.get('description', '').strip()
        contact = request.form.get('contact', '').strip()
        city = request.form.get('city', '').strip()
        price_range = request.form.get('price_range', '').strip()
        transaction_id = request.form.get('transaction_id', '').strip()  # EasyPaisa payment ID

        # Require payment
        if not transaction_id:
            flash(f"Please pay Rs. 2000 via EasyPaisa to {EASYPAYSA_NUMBER} and enter Transaction ID.", "danger")
            return render_template('provider_register.html', categories=categories, easypaisa_number=EASYPAYSA_NUMBER, form=request.form)

        # Save provider
        prov = Provider(
            name=name,
            category=category,
            description=description,
            contact=contact,
            city=city,
            price_range=price_range,
            approved=False,
            transaction_id=transaction_id
        )
        db.session.add(prov)
        db.session.commit()
        flash("Payment received. Your listing is submitted and pending admin approval.", "success")
        return redirect(url_for('thankyou'))

    return render_template('provider_register.html', categories=categories, easypaisa_number=EASYPAYSA_NUMBER, form={})

@app.route('/thankyou')
def thankyou():
    return render_template('thankyou.html')

@app.route('/provider/<int:provider_id>')
def provider_detail(provider_id):
    p = Provider.query.get_or_404(provider_id)
    return render_template('provider_detail.html', p=p)

# Simple admin (no auth) - for Phase1 only
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        action = request.form.get('action')
        pid = request.form.get('provider_id')
        if pid:
            prov = Provider.query.get(int(pid))
            if prov:
                if action == 'approve':
                    prov.approved = True
                    db.session.commit()
                    flash(f"Approved: {prov.name}", "success")
                elif action == 'reject':
                    db.session.delete(prov)
                    db.session.commit()
                    flash(f"Rejected and deleted: {prov.name}", "warning")
                elif action == 'unapprove':
                    prov.approved = False
                    db.session.commit()
                    flash(f"Unapproved: {prov.name}", "info")
        return redirect(url_for('admin'))

    providers = Provider.query.order_by(Provider.created_at.desc()).all()
    return render_template('admin.html', providers=providers)

# ---------- Init ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_categories()
    app.run(debug=True)
