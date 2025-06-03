from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import pandas as pd
from math import ceil
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder

app = Flask(__name__)
app.secret_key = 'MySecretKey'
login_manager = LoginManager(app)

# Pagination window helper
def get_pagination_window(current_page, total_pages, window=8):
    half = window // 2
    if total_pages <= window:
        return list(range(1, total_pages + 1))
    elif current_page <= half:
        return list(range(1, window + 1))
    elif current_page >= total_pages - half:
        return list(range(total_pages - window + 1, total_pages + 1))
    else:
        return list(range(current_page - half + 1, current_page + half + 1))

# User class for Flask-Login
class User(UserMixin):
    pass

@login_manager.user_loader
def user_loader(username):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user_data = c.fetchone()
    if not user_data:
        return None
    user = User()
    user.id = username
    user.role = user_data[3]
    return user

def get_user_id():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (current_user.id,))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

@app.route('/', methods=['GET', 'POST'])
def index():
    return student_login()

@app.route('/student/signup', methods=['GET', 'POST'])
def student_signup():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'student')",
                      (request.form['username'], request.form['password']))
            conn.commit()
            return redirect(url_for('student_login'))
        except sqlite3.IntegrityError:
            return 'Username already exists'
        finally:
            conn.close()
    return render_template('student_signup.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND role = 'student'", 
                  (request.form['username'],))
        user = c.fetchone()
        if user and user[2] == request.form['password']:
            user_obj = User()
            user_obj.id = user[1]
            login_user(user_obj)
            return redirect(url_for('profile'))
        return 'Invalid credentials'
    return render_template('student_login.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    uid = get_user_id()
    if request.method == 'POST':
        c.execute('''REPLACE INTO profiles 
                    (user_id, full_name, annual_income, hometown, college_name, college_location)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                  (uid, request.form['full_name'], request.form['annual_income'],
                   request.form['hometown'], request.form['college_name'], 
                   request.form['college_location']))
        conn.commit()
    c.execute("SELECT * FROM profiles WHERE user_id = ?", (uid,))
    profile = c.fetchone()
    conn.close()
    return render_template('profile.html', profile=profile)

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role, approved) VALUES (?, ?, 'admin', 0)",
                      (request.form['username'], request.form['password']))
            conn.commit()
            return "Registration submitted! Awaiting approval from an existing admin."
        except sqlite3.IntegrityError:
            return 'Username already exists'
        finally:
            conn.close()
    return render_template('admin_register.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND role = 'admin'", 
                  (request.form['username'],))
        user = c.fetchone()
        if user and user[2] == request.form['password']:
            if user[4] != 1:  # Assuming approved is the 5th column (index 4)
                return 'Your admin account is pending approval.'
            user_obj = User()
            user_obj.id = user[1]
            login_user(user_obj)
            return redirect(url_for('admin_dashboard'))
        return 'Invalid credentials'
    return render_template('admin_login.html')

@app.route('/admin/approve', methods=['GET', 'POST'])
@login_required
def admin_approve():
    if getattr(current_user, 'role', None) != 'admin':
        return redirect(url_for('admin_login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if request.method == 'POST':
        approve_ids = request.form.getlist('approve')
        for uid in approve_ids:
            c.execute("UPDATE users SET approved=1 WHERE id=?", (uid,))
        conn.commit()
    c.execute("SELECT id, username FROM users WHERE role='admin' AND approved=0")
    pending_admins = c.fetchall()
    conn.close()
    return render_template('admin_approve.html', pending_admins=pending_admins)

@app.route('/admin/approve_single/<int:user_id>')
@login_required
def approve_single_admin(user_id):
    if getattr(current_user, 'role', None) != 'admin':
        return redirect(url_for('admin_login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("UPDATE users SET approved=1 WHERE id=? AND role='admin' AND approved=0", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_approve'))

@app.route('/admin/delete_request/<int:user_id>')
@login_required
def delete_admin_request(user_id):
    if getattr(current_user, 'role', None) != 'admin':
        return redirect(url_for('admin_login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # Only allow deleting unapproved admins
    c.execute("DELETE FROM users WHERE id=? AND role='admin' AND approved=0", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_approve'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if getattr(current_user, 'role', None) != 'admin':
        return redirect(url_for('admin_login'))
    page = request.args.get('page', 1, type=int)
    per_page = 10
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM profiles")
    total = c.fetchone()[0]
    c.execute('''SELECT profiles.*, users.username 
                 FROM profiles JOIN users ON profiles.user_id = users.id
                 LIMIT ? OFFSET ?''', (per_page, (page-1)*per_page))
    students = c.fetchall()
    conn.close()
    total_pages = ceil(total/per_page) if total else 1
    pagination_window = get_pagination_window(page, total_pages, window=8)
    return render_template('admin_dashboard.html', 
                           students=students, 
                           total_pages=total_pages,
                           current_page=page,
                           pagination_window=pagination_window)

@app.route('/admin/delete/<int:user_id>')
@login_required
def admin_delete(user_id):
    if getattr(current_user, 'role', None) != 'admin':
        return redirect(url_for('admin_login'))
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/search', methods=['GET', 'POST'])
@login_required
def admin_search():
    if getattr(current_user, 'role', None) != 'admin':
        return redirect(url_for('admin_login'))
    page = request.args.get('page', 1, type=int)
    per_page = 10

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    income_groups = [
        ('<4.8L', 'annual_income < 480000'),
        ('4.8L-7.7L', 'annual_income BETWEEN 480000 AND 770000'),
        ('7.7L-10.2L', 'annual_income BETWEEN 770000 AND 1020000'),
        ('10.2L-13.8L', 'annual_income BETWEEN 1020000 AND 1380000'),
        ('>13.8L', 'annual_income > 1380000')
    ]
    c.execute("SELECT DISTINCT college_location FROM profiles")
    college_locations = sorted([row[0] for row in c.fetchall()])

    filters = []
    params = []
    if request.method == 'POST':
        if request.form.get('hometown'):
            filters.append("hometown = ?")
            params.append(request.form['hometown'])
        if request.form.get('college_name'):
            filters.append("college_name = ?")
            params.append(request.form['college_name'])
        if request.form.get('income_group'):
            selected_group = next(g for g in income_groups if g[0] == request.form['income_group'])
            filters.append(selected_group[1])
        if request.form.get('student_name'):
            filters.append("full_name LIKE ?")
            params.append(f"%{request.form['student_name']}%")
        if request.form.get('college_location'):
            filters.append("college_location = ?")
            params.append(request.form['college_location'])
    query = '''SELECT * FROM profiles'''
    count_query = '''SELECT COUNT(*) FROM profiles'''
    if filters:
        filter_str = ' WHERE ' + ' AND '.join(filters)
        query += filter_str
        count_query += filter_str
    c.execute(count_query, params)
    total = c.fetchone()[0]
    query += ' LIMIT ? OFFSET ?'
    c.execute(query, params + [per_page, (page-1)*per_page])
    results = c.fetchall()
    # --- Correct median logic using pandas ---
    incomes = [row[2] for row in results if row[2] is not None]
    if incomes:
        median_income = float(pd.Series(incomes).median())
        min_income = min(incomes)
        max_income = max(incomes)
    else:
        median_income = min_income = max_income = 0
    stats = {
        'min': min_income,
        'max': max_income,
        'median': median_income
    }
    # --- End median logic ---
    conn.close()
    total_pages = ceil(total/per_page) if total else 1
    pagination_window = get_pagination_window(page, total_pages, window=8)
    return render_template('admin_search.html',
                           results=results,
                           stats=stats,
                           income_groups=income_groups,
                           total_pages=total_pages,
                           current_page=page,
                           pagination_window=pagination_window,
                           college_locations=college_locations)

@app.template_filter('comma_format')
def comma_format_filter(value):
    try:
        return "{:,}".format(int(value))
    except Exception:
        return value

@app.route('/admin/predict', methods=['GET', 'POST'])
@login_required
def admin_predict():
    if getattr(current_user, 'role', None) != 'admin':
        return redirect(url_for('admin_login'))

    prediction = None
    error = None
    recommended_colleges = []
    recommended_hometowns = []

    # Get all hometowns and college locations for dropdowns
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT hometown FROM profiles")
    hometowns = sorted([row[0] for row in c.fetchall()])
    c.execute("SELECT DISTINCT college_location FROM profiles")
    college_locations = sorted([row[0] for row in c.fetchall()])
    conn.close()

    if request.method == 'POST':
        hometown = request.form.get('hometown', '').strip()
        college_loc = request.form.get('college_location', '').strip()
        income = request.form.get('annual_income', '').strip()
        income = int(income) if income else None

        # Load live data from database
        conn = sqlite3.connect('database.db')
        df = pd.read_sql_query("SELECT * FROM profiles", conn)
        conn.close()

        if df.empty:
            error = "No data available."
        elif not (hometown or college_loc or income is not None):
            error = "Please provide at least one input (Hometown, College Location, or Annual Income)."
        else:
            try:
                # Dynamically build features and encoders
                features = []
                input_data = []
                encoders = {}

                # Determine what we're predicting
                predict_college = True  # default
                predict_hometown = False

                # If only college location is given, predict hometown
                if college_loc and not hometown and income is None:
                    predict_college = False
                    predict_hometown = True

                # Prepare features and encode
                if hometown:
                    le_hometown = LabelEncoder()
                    df = df.dropna(subset=['hometown'])
                    df['Hometown_encoded'] = le_hometown.fit_transform(df['hometown'])
                    features.append('Hometown_encoded')
                    encoders['hometown'] = le_hometown
                if college_loc:
                    le_college_loc = LabelEncoder()
                    df = df.dropna(subset=['college_location'])
                    df['CollegeLoc_encoded'] = le_college_loc.fit_transform(df['college_location'])
                    features.append('CollegeLoc_encoded')
                    encoders['college_loc'] = le_college_loc
                if income is not None:
                    df = df.dropna(subset=['annual_income'])
                    features.append('annual_income')

                # Prepare input_data in order
                input_data = []
                for feat in features:
                    if feat == 'Hometown_encoded':
                        if hometown in encoders['hometown'].classes_:
                            input_data.append(encoders['hometown'].transform([hometown])[0])
                        else:
                            error = "Hometown not found in training data"
                            break
                    elif feat == 'CollegeLoc_encoded':
                        if college_loc in encoders['college_loc'].classes_:
                            input_data.append(encoders['college_loc'].transform([college_loc])[0])
                        else:
                            error = "College location not found in training data"
                            break
                    elif feat == 'annual_income':
                        input_data.append(int(income))
                else:
                    # Drop rows with missing values in any selected features or target
                    drop_cols = []
                    if 'Hometown_encoded' in features:
                        drop_cols.append('hometown')
                    if 'CollegeLoc_encoded' in features:
                        drop_cols.append('college_location')
                    if 'annual_income' in features:
                        drop_cols.append('annual_income')
                    if predict_college:
                        drop_cols.append('college_name')
                    else:
                        drop_cols.append('hometown')
                    df = df.dropna(subset=drop_cols)

                    # Prepare X and y
                    if predict_college:
                        y = df['college_name']
                    else:
                        y = df['hometown']
                    X = df[features]

                    # Encode y if needed
                    le_target = LabelEncoder()
                    y_enc = le_target.fit_transform(y)

                    # Use LogisticRegression if enough data, else fallback to groupby/mode
                    if not X.empty and len(set(y_enc)) > 1 and len(X) >= 5:
                        model = LogisticRegression(multi_class='multinomial', max_iter=1000)
                        model.fit(X, y_enc)
                        pred_enc = model.predict([input_data])[0]
                        confidence = model.predict_proba([input_data]).max()
                        pred_value = le_target.inverse_transform([pred_enc])[0]
                        used_model = "LogisticRegression"
                    else:
                        # Fallback to groupby/mode
                        filtered = df.copy()
                        if hometown:
                            filtered = filtered[filtered['hometown'] == hometown]
                        if college_loc:
                            filtered = filtered[filtered['college_location'] == college_loc]
                        if income is not None:
                            filtered = filtered[abs(filtered['annual_income'] - income) <= 50000]
                        if predict_college:
                            if not filtered.empty:
                                pred_value = filtered['college_name'].mode().iloc[0]
                                confidence = "majority"
                                used_model = "Majority"
                            else:
                                pred_value = None
                        else:
                            if not filtered.empty:
                                pred_value = filtered['hometown'].mode().iloc[0]
                                confidence = "majority"
                                used_model = "Majority"
                            else:
                                pred_value = None

                    if pred_value:
                        if predict_college:
                            college_df = df[df['college_name'] == pred_value]
                            student_count = len(college_df)
                            avg_income = int(college_df['annual_income'].mean()) if not college_df.empty else 0
                            common_hometowns = college_df['hometown'].value_counts().head(3).items()
                            prediction = {
                                'college': pred_value,
                                'confidence': confidence if used_model == "majority" else f"{confidence:.1%}",
                                'student_count': student_count,
                                'avg_income': avg_income,
                                'common_hometowns': list(common_hometowns),
                                'type': 'college',
                                'used_model': used_model
                            }
                            if college_loc:
                                recommended_colleges = sorted(df[df['college_location'] == college_loc]['college_name'].unique())
                        else:
                            home_df = df[df['hometown'] == pred_value]
                            student_count = len(home_df)
                            avg_income = int(home_df['annual_income'].mean()) if not home_df.empty else 0
                            common_colleges = home_df['college_name'].value_counts().head(3).items()
                            prediction = {
                                'hometown': pred_value,
                                'confidence': confidence if used_model == "majority" else f"{confidence:.1%}",
                                'student_count': student_count,
                                'avg_income': avg_income,
                                'common_colleges': list(common_colleges),
                                'type': 'hometown',
                                'used_model': used_model
                            }
                            if college_loc:
                                recommended_hometowns = sorted(df[df['college_location'] == college_loc]['hometown'].unique())
                    else:
                        error = "No matching data found for your input."

            except Exception as e:
                if not error:
                    error = f"Prediction error: {str(e)}"

    return render_template('admin_predict.html', 
                         prediction=prediction,
                         error=error,
                         hometowns=hometowns,
                         college_locations=college_locations,
                         recommended_colleges=recommended_colleges,
                         recommended_hometowns=recommended_hometowns)
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
