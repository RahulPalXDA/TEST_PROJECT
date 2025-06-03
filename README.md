# Student & College Analytics Portal

A Flask web application for student registration, profile management, and admin analytics with live machine learning predictions and advanced search. Includes Bootstrap UI, pagination, and robust admin features.

---

## Features

- **Student Registration & Login**
- **Profile Management** (Full Name, Annual Income, Hometown, College Name, College Location)
- **Admin Registration & Login**
- **Admin Dashboard** with paginated student table (10 per page), search, and delete
- **Advanced Search**: Filter by student name, hometown, college name, college location, income group, with delete and pagination
- **Machine Learning Prediction**: Predict likely college (or hometown) using LogisticRegression, with groupby fallback and confidence
- **Bootstrap 5 UI**: Responsive and modern
- **Logout** for both students and admins

---

## Setup

1. **Clone the repository:**
    ```
    git clone <your-repo-url>
    cd <your-repo-directory>
    ```

2. **Install dependencies:**
    ```
    pip install -r requirements.txt
    ```

3. **Initialize the database:**
    ```
    python db.py
    ```

4. **Run the app:**
    ```
    python app.py
    ```

5. **Open in your browser:**
    ```
    http://localhost:5000/
    ```

---

## Usage

- **Students:** Sign up and log in at `/` (homepage), manage your profile.
- **Admins:** Register or log in at `/admin/login` or `/admin/register`, access dashboard and analytics.
- **Advanced Search:** Use `/admin/search` for multi-criteria search and deletion.
- **Prediction:** Use `/admin/predict` to predict likely college/hometown for given inputs.

---

## Default Admin

- Register a new admin via `/admin/register` or insert directly into the database.

---

## File Structure

```your_project/
├── app.py
├── db.py
├── requirements.txt
├── README.md
└── templates/
├── student_signup.html
├── student_login.html
├── profile.html
├── admin_login.html
├── admin_register.html
├── admin_dashboard.html
├── admin_search.html
├── admin_predict.html
└── pagination.html```


---

## Tech Stack

- Python 3.8+
- Flask
- Flask-Login
- SQLite3
- Pandas
- scikit-learn
- Bootstrap 5 (CDN)
