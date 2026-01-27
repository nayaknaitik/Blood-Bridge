from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime

app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend/static'
)

app.secret_key = "blood_bridge_secret_key"

# MongoDB Configuration
app.config["MONGO_URI"] = "mongodb://localhost:27017/bloodbridge"
mongo = PyMongo(app)

# Helper to ensure users have blood_group populated based on donations
def enrich_users_with_blood_group(users):
    """
    For users who don't have a blood_group stored,
    try to infer it from their latest donation and persist it.
    """
    for user in users:
        try:
            if not user.get('blood_group'):
                user_id_str = str(user['_id'])
                latest_donation = mongo.db.donations.find_one(
                    {"donor_id": user_id_str},
                    sort=[("date", -1), ("_id", -1)]
                )
                if latest_donation and latest_donation.get('blood_group'):
                    user['blood_group'] = latest_donation['blood_group']
                    mongo.db.users.update_one(
                        {"_id": user['_id']},
                        {"$set": {"blood_group": latest_donation['blood_group']}}
                    )
        except Exception:
            # Avoid breaking dashboard if anything goes wrong for a single user
            continue
    return users
# -------------------- Routes --------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        users = mongo.db.users

        hashed_password = generate_password_hash(request.form['password'])

        users.insert_one({
            'name': request.form['name'],
            'email': request.form['email'],
            'password': hashed_password,
            # no role stored at signup for normal users
            'blood_group': request.form.get('blood_group')
        })

        flash('Registration successful!')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        user = users.find_one({'email': request.form['email']})

        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = str(user['_id'])
            session['name'] = user['name']
            session['user_email'] = user.get('email')
            # Preserve any special roles (admin / bloodbank) if they exist
            session['role'] = user.get('role')

            # Normal users: go to role selection page
            if user.get('role') in ['admin', 'bloodbank']:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('choose_role'))

        flash('Invalid email or password')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    # Always fetch the latest user document
    user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    if not user:
        session.clear()
        return redirect(url_for('login'))

    role = user.get('role')  # only used for special accounts (admin / bloodbank)
    current_role = user.get('current_role') or session.get('current_role')

    # -------- Normal user flows: donor / recipient via current_role --------
    if role not in ['admin', 'bloodbank']:
        if current_role == 'donor':
            # Fetch all donations for this user, sorted by date (newest first)
            user_donations = list(
                mongo.db.donations.find({"donor_id": user_id}).sort([("date", -1), ("_id", -1)])
            )
            session['current_role'] = 'donor'
            return render_template('donor_dashboard.html', donations=user_donations)

        if current_role == 'recipient':
            # Fetch this user's blood requests
            user_requests = list(
                mongo.db.blood_requests.find({"requester_id": user_id}).sort("timestamp", -1)
            )

            # Calculate inventory for availability check
            blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
            inventory = {}

            for bg in blood_groups:
                # Count available donations with this blood group
                units = mongo.db.donations.count_documents({
                    "blood_group": bg,
                    "status": {"$in": ["Scheduled", "Completed"]}
                })
                inventory[bg] = units

            # Add availability info to each request
            requests_with_availability = []
            for req in user_requests:
                requested_bg = req.get('blood_group', '') or ''

                # Safely convert units to int
                try:
                    units_value = req.get('units', 0)
                    if isinstance(units_value, str):
                        requested_units = int(units_value) if units_value.isdigit() else 0
                    else:
                        requested_units = int(units_value) if units_value else 0
                except (ValueError, TypeError):
                    requested_units = 0

                available_units = inventory.get(requested_bg, 0)

                # Format timestamp safely
                timestamp = req.get('timestamp')
                if timestamp:
                    if isinstance(timestamp, datetime):
                        timestamp_str = timestamp.strftime('%Y-%m-%d')
                    else:
                        timestamp_str = str(timestamp)[:10] if len(str(timestamp)) >= 10 else 'N/A'
                else:
                    timestamp_str = 'N/A'

                req_dict = {
                    '_id': str(req.get('_id', '')),
                    'patient_name': req.get('patient_name', 'N/A'),
                    'blood_group': requested_bg,
                    'units': requested_units,
                    'hospital': req.get('hospital', 'N/A'),
                    'status': req.get('status', 'pending'),
                    'timestamp': timestamp_str,
                    'timestamp_obj': timestamp,  # Keep original for sorting if needed
                    'available_units': available_units,
                    'is_available': available_units >= requested_units if requested_units > 0 else False
                }
                requests_with_availability.append(req_dict)

            session['current_role'] = 'recipient'
            return render_template(
                'recipient_dashboard.html',
                requests=requests_with_availability,
                inventory=inventory
            )

        # If no current_role chosen yet, send user to role-selection
        return redirect(url_for('choose_role'))

    # -------- Blood bank & admin flows (special accounts) --------
    if role == 'bloodbank':
        # Fetch latest 5 donors from donations collection
        recent_donors_list = list(
            mongo.db.donations.find(
                {},
                {"_id": 0, "donor_name": 1, "blood_group": 1, "date": 1, "location": 1}
            )
            .sort("date", -1)
            .limit(5)
        )
        
        # Format donors data for template
        formatted_donors = []
        for d in recent_donors_list:
            formatted_donors.append({
                'name': d.get('donor_name', 'Unknown'),
                'blood_group': d.get('blood_group', 'N/A'),
                'last_donation': d.get('date', 'N/A')
            })

        # Calculate inventory from donations
        blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        inventory = []
        total_units = 0
        
        for bg in blood_groups:
            # Count donations with this blood group and status Completed or Scheduled
            units = mongo.db.donations.count_documents({
                "blood_group": bg,
                "status": {"$in": ["Scheduled", "Completed"]}
            })
            total_units += units
            inventory.append({
                'group': bg,
                'units': units
            })

        # Get today's date string for filtering
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_donations = mongo.db.donations.count_documents({"date": today_str})
        
        # Get recent requests
        recent_requests = list(mongo.db.blood_requests.find({"status": "pending"}).limit(10))

        donors_count = len(mongo.db.donations.distinct('donor_id'))

        stats = {
            'total_donors': donors_count,
            'pending_requests': mongo.db.blood_requests.count_documents({'status': 'pending'}),
            'total_units': total_units,
            'today_donations': today_donations
        }

        return render_template(
            'bloodbank_dashboard.html',
            stats=stats,
            donors=formatted_donors,
            inventory=inventory,
            requests=recent_requests,
            today=datetime.now().strftime("%d %b %Y")
        )

    else:  # admin
        users = list(mongo.db.users.find())
        users = enrich_users_with_blood_group(users)
        blood_requests = list(mongo.db.blood_requests.find().sort("timestamp", -1))
        all_donations = list(mongo.db.donations.find().sort("date", -1))

        # Calculate inventory
        blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
        inventory = []
        total_inventory_units = 0
        
        for bg in blood_groups:
            units = mongo.db.donations.count_documents({
                "blood_group": bg,
                "status": {"$in": ["Scheduled", "Completed"]}
            })
            total_inventory_units += units
            inventory.append({
                'group': bg,
                'units': units
            })

        # Calculate today's donations
        today_str = datetime.now().strftime("%Y-%m-%d")
        today_donations_count = mongo.db.donations.count_documents({"date": today_str})
        
        # Pending requests count
        pending_requests_count = mongo.db.blood_requests.count_documents({'status': 'pending'})
        completed_requests_count = mongo.db.blood_requests.count_documents({'status': 'fulfilled'})

        donors_count = len(mongo.db.donations.distinct('donor_id'))
        recipients_count = len(mongo.db.blood_requests.distinct('requester_id'))

        stats = {
            'total_users': len(users),
            'donors_count': donors_count,
            'recipients_count': recipients_count,
            'banks_count': mongo.db.users.count_documents({'role': 'bloodbank'}),
            'total_requests': len(blood_requests),
            'pending_requests': pending_requests_count,
            'completed_requests': completed_requests_count,
            'total_donations': len(all_donations),
            'today_donations': today_donations_count,
            'total_inventory': total_inventory_units
        }

        return render_template('admin_dashboard.html', 
                             users=users, 
                             requests=blood_requests, 
                             donations=all_donations[:10],  # Latest 10 donations
                             inventory=inventory,
                             stats=stats)


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('role') != 'admin':
        flash("Unauthorized access!")
        return redirect(url_for('login'))

    all_users = list(mongo.db.users.find())
    all_users = enrich_users_with_blood_group(all_users)
    all_requests = list(mongo.db.blood_requests.find().sort("timestamp", -1))
    all_donations = list(mongo.db.donations.find().sort("date", -1))

    # Calculate inventory
    blood_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
    inventory = []
    total_inventory_units = 0
    
    for bg in blood_groups:
        units = mongo.db.donations.count_documents({
            "blood_group": bg,
            "status": {"$in": ["Scheduled", "Completed"]}
        })
        total_inventory_units += units
        inventory.append({
            'group': bg,
            'units': units
        })

    # Calculate today's donations
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_donations_count = mongo.db.donations.count_documents({"date": today_str})
    
    # Pending requests count
    pending_requests_count = mongo.db.blood_requests.count_documents({'status': 'pending'})
    completed_requests_count = mongo.db.blood_requests.count_documents({'status': 'fulfilled'})

    donors_count = len(mongo.db.donations.distinct('donor_id'))
    recipients_count = len(mongo.db.blood_requests.distinct('requester_id'))

    dashboard_stats = {
        'total_users': len(all_users),
        'donors_count': donors_count,
        'recipients_count': recipients_count,
        'banks_count': mongo.db.users.count_documents({'role': 'bloodbank'}),
        'total_requests': len(all_requests),
        'pending_requests': pending_requests_count,
        'completed_requests': completed_requests_count,
        'total_donations': len(all_donations),
        'today_donations': today_donations_count,
        'total_inventory': total_inventory_units
    }

    return render_template(
        'admin_dashboard.html',
        users=all_users,
        requests=all_requests,
        donations=all_donations[:10],  # Latest 10 donations
        inventory=inventory,
        stats=dashboard_stats
    )


@app.route('/delete_user/<user_id>', methods=['POST'])
def delete_user(user_id):
    if session.get('role') == 'admin':
        mongo.db.users.delete_one({'_id': ObjectId(user_id)})
        flash("User removed successfully.")
    return redirect(url_for('admin_dashboard'))


@app.route('/choose_role', methods=['GET', 'POST'])
def choose_role():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = mongo.db.users.find_one({'_id': ObjectId(session['user_id'])})
    if not user:
        session.clear()
        return redirect(url_for('login'))

    # Special accounts skip role selection
    if user.get('role') in ['admin', 'bloodbank']:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        role_choice = request.form.get('role_choice')
        if role_choice not in ['donor', 'recipient']:
            flash('Please choose how you want to use BloodBridge.')
            return redirect(url_for('choose_role'))

        mongo.db.users.update_one(
            {'_id': user['_id']},
            {'$set': {'current_role': role_choice}}
        )
        session['current_role'] = role_choice
        return redirect(url_for('dashboard'))

    return render_template('choose_role.html')

@app.route('/request_blood')
def request_blood():
    if 'user_id' not in session:
        flash("Please login to request blood.")
        return redirect(url_for('login'))
    return render_template('request_blood.html')


@app.route('/submit_blood_request', methods=['POST'])
def submit_blood_request():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    new_request = {
        "requester_id": session['user_id'],
        "patient_name": request.form.get('patient_name'),
        "blood_group": request.form.get('blood_group'),
        "units": request.form.get('units'),
        "hospital": request.form.get('hospital'),
        "status": "pending",
        "timestamp": datetime.now()
    }

    mongo.db.blood_requests.insert_one(new_request)
    flash("Blood request has been posted successfully!")
    return redirect(url_for('dashboard'))


@app.route('/schedule_donation')
def schedule_donation():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('schedule_donation.html')
@app.route('/submit_donation_slot', methods=['POST'])
def submit_donation_slot():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Read blood group from form, fallback to None if not selected
    blood_group = request.form.get('blood_group')
    if not blood_group:
        flash("Please select a blood group!")
        return redirect(url_for('schedule_donation'))

    donation_data = {
        "donor_id": session['user_id'],
        "donor_name": session['name'],
        "blood_group": blood_group,  # <-- use the form value
        "date": request.form.get('donation_date'),
        "location": request.form.get('location'),
        "time_slot": request.form.get('time_slot'),
        "status": "Scheduled"
    }

    mongo.db.donations.insert_one(donation_data)
    flash("Success! Your donation slot has been scheduled.")
    return redirect(url_for('dashboard'))




@app.route('/view_requests')
def view_requests():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    requests = list(mongo.db.blood_requests.find({'status': 'pending'}))
    return render_template('view_requests_for_donors.html', requests=requests)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        contact_data = {
            "name": request.form.get('name'),
            "email": request.form.get('email'),
            "subject": request.form.get('subject'),
            "message": request.form.get('message'),
            "timestamp": datetime.now()
        }

        mongo.db.messages.insert_one(contact_data)
        flash("Thank you! Your message has been sent successfully.")
        return redirect(url_for('contact'))

    return render_template('contact.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)

