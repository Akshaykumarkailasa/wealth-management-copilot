'''from flask import Flask, render_template, request, session, redirect
from db import conn, cursor
import bcrypt
from portfolio_engine import get_portfolio
from dotenv import load_dotenv

load_dotenv()
from gemini_helper import ask_gemini
from sklearn.linear_model import LinearRegression
import numpy as np
from flask import send_file
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak
)

from reportlab.lib import colors

import matplotlib.pyplot as plt

def log_ai_usage(user_id, feature):

    cursor.execute(
        """
        INSERT INTO ai_logs
        (
            user_id,
            feature_used
        )
        VALUES(%s,%s)
        """,
        (
            user_id,
            feature
        )
    )

    conn.commit()

app = Flask(__name__)
import os

app.secret_key = os.getenv("SECRET_KEY")
def forecast_expense(user_id):

    cursor.execute(
        """
        SELECT amount
        FROM expenses
        WHERE user_id=%s
        ORDER BY expense_date
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    if len(rows) < 2:
        return None

    X = []
    y = []

    for i, row in enumerate(rows):

        X.append([i + 1])

        y.append(float(row["amount"]))

    model = LinearRegression()

    model.fit(X, y)

    next_month = [[len(rows) + 1]]

    prediction = model.predict(next_month)

    return round(float(prediction[0]), 2)

@app.route("/")
def home():
    return render_template("index.html")
@app.route("/report")
def report():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id=%s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.execute(
        """
        SELECT SUM(amount) AS total
        FROM expenses
        WHERE user_id=%s
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    expense = float(result["total"] or 0)

    savings = float(user["income"]) - expense

    if float(user["income"]) > 0:

        health_score = round(
            (savings / float(user["income"])) * 100
        )

    else:

        health_score = 0

    risk = session.get(
        "risk_type",
        "Not Assessed"
    )

    forecast = abs(
    forecast_expense(user_id)
) if forecast_expense(user_id) is not None else None

    cursor.execute(
        """
        SELECT *
        FROM goals
        WHERE user_id=%s
        ORDER BY id DESC
        """,
        (user_id,)
    )

    goals = cursor.fetchall()

    if risk == "Conservative":

        portfolio = {
            "Bonds": 50,
            "Mutual Funds": 25,
            "Stocks": 15,
            "Gold": 10
        }

    elif risk == "Moderate":

        portfolio = {
            "Stocks": 50,
            "Mutual Funds": 25,
            "Bonds": 15,
            "Gold": 10
        }

    else:

        portfolio = {
            "Stocks": 70,
            "Mutual Funds": 15,
            "Gold": 10,
            "Bonds": 5
        }

    pdf_file = "financial_report.pdf"

    doc = SimpleDocTemplate(pdf_file)

    styles = getSampleStyleSheet()

    elements = []
    elements.append(
    Paragraph(
        "WEALTH MANAGEMENT REPORT",
        styles["Title"]
    )
)

    elements.append(
    Paragraph(
        "AI Powered Personal Finance Analysis",
        styles["Heading3"]
    )
)

    elements.append(Spacer(1,20))
    elements.append(
    Paragraph(
        "Executive Summary",
        styles["Heading2"]
    )
)

    elements.append(
    Paragraph(
        f"""
This report analyzes the financial
position of {user['name']}.

Current savings amount to
Rs. {savings:,.0f} with a
Financial Health Score of
{health_score}/100.

Risk Profile:
{risk}
        """,
        styles["Normal"]
    )
)

    elements.append(
    Spacer(1,10)
)
    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph(
            "User Profile",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            f"Name: {user['name']}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Age: {user['age']}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Income: Rs. {user['income']:,.0f}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Financial Summary",
            styles["Heading2"]
        )
    )
    if health_score >= 70:

        recommendation = """
Excellent financial discipline.

Continue investing regularly and
focus on portfolio diversification.
"""

    elif health_score >= 40:

        recommendation = """
    Moderate financial health.

    Increase monthly savings and
    review discretionary spending.
    """

    else:

        recommendation = """
    Financial health requires attention.

    Reduce expenses and establish
    a stronger savings habit.
    """
    elements.append(
        Paragraph(
            "Recommendations",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            recommendation,
            styles["Normal"]
        )
    )
    elements.append(
        Paragraph(
            f"Total Expenses: ₹{expense}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Savings: ₹{savings}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Health Score: {health_score}/100",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Risk Assessment",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            f"Risk Profile: {risk}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Portfolio Recommendation",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            "Recommended Allocation",
            styles["Heading3"]
        )
    )

    for asset,value in portfolio.items():

        elements.append(
            Paragraph(
                f"• {asset}: {value}%",
                styles["Normal"]
            )
        )
    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Machine Learning Forecast",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            f"Predicted Next Expense: ₹{forecast if forecast is not None else 'Not Available'}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Financial Goals",
            styles["Heading2"]
        )
    )

    if goals:

        for g in goals:

            elements.append(
                Paragraph(
                    f"{g['goal_name']} - ₹{g['target_amount']} ({g['years']} Years)",
                    styles["Normal"]
                )
            )

    else:

        elements.append(
            Paragraph(
                "No goals created yet.",
                styles["Normal"]
            )
        )
    cursor.execute(
        """
        SELECT category,
            SUM(amount) total
        FROM expenses
        WHERE user_id=%s
        GROUP BY category
        """,
        (user_id,)
    )

    expense_data = cursor.fetchall()

    if expense_data:

        labels = [
            row["category"]
            for row in expense_data
        ]

        values = [
            float(row["total"])
            for row in expense_data
        ]

        plt.figure(figsize=(5,5))

        plt.pie(
            values,
            labels=labels,
            autopct="%1.1f%%"
        )

        plt.title(
            "Expense Distribution"
        )

        chart_file = "expense_chart.png"

        plt.savefig(chart_file)

        plt.close()

        elements.append(
            PageBreak()
        )

        elements.append(
            Paragraph(
                "Expense Distribution",
                styles["Heading2"]
            )
        )

        elements.append(
            Image(
                chart_file,
                width=300,
                height=300
            )
        )
# ---------------- PORTFOLIO CHART ----------------

    portfolio_labels = list(
        portfolio.keys()
    )

    portfolio_values = list(
        portfolio.values()
    )

    plt.figure(figsize=(5,5))

    plt.pie(
        portfolio_values,
        labels=portfolio_labels,
        autopct="%1.1f%%"
    )

    plt.title(
        "Portfolio Allocation"
    )

    portfolio_chart = "portfolio_chart.png"

    plt.savefig(
        portfolio_chart
    )

    plt.close()

    elements.append(
        PageBreak()
    )

    elements.append(
        Paragraph(
            "Portfolio Allocation Analysis",
            styles["Heading2"]
        )
    )

    elements.append(
        Image(
            portfolio_chart,
            width=300,
            height=300
        )
    )
    doc.build(elements)

    return send_file(
        pdf_file,
        as_attachment=True
    )
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        age = request.form["age"]
        income = request.form["income"]

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email=%s
            """,
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            return "Email already registered. Please login."

        hashed_password = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        )

        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password,
                age,
                income
            )
            VALUES(%s,%s,%s,%s,%s)
            """,
            (
                name,
                email,
                hashed_password.decode(),
                age,
                income
            )
        )

        conn.commit()

        return redirect("/login")

    return render_template("register.html")
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        query = """
        SELECT * FROM users
        WHERE email=%s
        """

        cursor.execute(query,(email,))

        user = cursor.fetchone()

        if user:

            if bcrypt.checkpw(
                password.encode(),
                user["password"].encode()
            ):

                session["user_id"] = user["id"]

                return redirect("/dashboard")

        return "Invalid Credentials"

    return render_template("login.html")
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    # ---------------- USER DETAILS ----------------

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id=%s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    # ---------------- TOTAL EXPENSES ----------------

    cursor.execute(
        """
        SELECT SUM(amount) AS total
        FROM expenses
        WHERE user_id=%s
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    total_expense = float(
        result["total"] or 0
    )

    income = float(
        user["income"]
    )

    savings = income - total_expense

    # ---------------- HEALTH SCORE ----------------

    if income > 0:

        savings_ratio = savings / income

        health_score = max(
            0,
            min(
                100,
                round(savings_ratio * 100)
            )
        )

    else:

        health_score = 0
    

    if health_score < 40:

        recommendation = """
        Expenses are consuming a large
        percentage of income.

        Reduce discretionary spending
        and increase savings.
        """

    elif health_score < 70:

        recommendation = """
        Financial position is stable.

        Consider increasing investment
        contributions.
        """

    else:

        recommendation = """
        Strong financial health.

        Focus on wealth growth and
        portfolio diversification.
        """
    
    # ---------------- AI FINANCIAL INSIGHT ----------------

    risk_type = session.get(
    "risk_type",
    "Not Assessed"
    )

    expense_ratio = (
    total_expense / income
    ) if income > 0 else 0

    if health_score < 40:

        ai_insight = f"""
📉 Financial Health: Needs Improvement

• Expenses consume {round(expense_ratio*100)}% of your income.

• Current savings are ₹{savings:,.0f}.

• Your spending pattern may affect long-term wealth creation.

Recommendation:
Reduce discretionary expenses and
increase monthly savings.

Next Action:
Create a monthly budget and aim
to save at least 20% of income.
"""

    elif health_score < 70:

        ai_insight = f"""
📊 Financial Health: Moderate

• Savings currently stand at ₹{savings:,.0f}.

• Financial position is stable but has room for improvement.

• Your risk profile is {risk_type}.

Recommendation:
Increase investments gradually and
maintain spending discipline.

Next Action:
Allocate an additional 10% of income
towards long-term investments.
"""

    else:

        ai_insight = f"""
🚀 Financial Health: Strong

• Savings of ₹{savings:,.0f} indicate strong financial discipline.

• Spending is well controlled relative to income.

• Your risk profile is {risk_type}.

Recommendation:
Focus on portfolio diversification
and long-term wealth accumulation.

Next Action:
Review investment allocation and
increase exposure to growth assets.
"""

    # ---------------- EXPENSE HISTORY ----------------

    cursor.execute(
        """
        SELECT *
        FROM expenses
        WHERE user_id=%s
        ORDER BY expense_date DESC
        """,
        (user_id,)
    )

    expenses = cursor.fetchall()

    # ---------------- CHART DATA ----------------

    cursor.execute(
        """
        SELECT
            category,
            SUM(amount) AS total
        FROM expenses
        WHERE user_id=%s
        GROUP BY category
        """,
        (user_id,)
    )

    chart_data = cursor.fetchall()

    # ---------------- ML FORECAST ----------------

    forecast = forecast_expense(
        user_id
    )

    return render_template(
        "dashboard.html",
        user=user,
        expense=total_expense,
        savings=savings,
        expenses=expenses,
        health_score=health_score,
        chart_data=chart_data,
        ai_insight=ai_insight,
        forecast=forecast
    )
@app.route("/expense", methods=["GET","POST"])
def expense():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        category = request.form["category"]

        amount = request.form["amount"]

        expense_date = request.form["expense_date"]

        query = """
        INSERT INTO expenses
        (
            user_id,
            category,
            amount,
            expense_date
        )
        VALUES(%s,%s,%s,%s)
        """

        cursor.execute(
            query,
            (
                session["user_id"],
                category,
                amount,
                expense_date
            )
        )

        conn.commit()

        return redirect("/dashboard")

    return render_template("expense.html")
@app.route("/risk", methods=["GET", "POST"])
def risk():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        score = (
            int(request.form["q1"]) +
            int(request.form["q2"]) +
            int(request.form["q3"]) +
            int(request.form["q4"]) +
            int(request.form["q5"]) +
            int(request.form["q6"]) +
            int(request.form["q7"]) +
            int(request.form["q8"])
        )

        if score <= 12:
            risk_type = "Conservative"

        elif score <= 18:
            risk_type = "Moderate"

        else:
            risk_type = "Aggressive"

        session["risk_type"] = risk_type

        return redirect("/portfolio")

    return render_template("risk.html")
@app.route("/portfolio")
def portfolio():

    if "user_id" not in session:
        return redirect("/login")

    risk = session.get("risk_type")

    if not risk:
        return redirect("/risk")

    if risk == "Conservative":

        portfolio = {
            "Bonds": 50,
            "Mutual Funds": 25,
            "Stocks": 15,
            "Gold": 10
        }

    elif risk == "Moderate":

        portfolio = {
            "Stocks": 50,
            "Mutual Funds": 25,
            "Bonds": 15,
            "Gold": 10
        }

    else:

        portfolio = {
            "Stocks": 70,
            "Mutual Funds": 15,
            "Gold": 10,
            "Bonds": 5
        }

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id=%s
        """,
        (session["user_id"],)
    )

    user = cursor.fetchone()

    try:

        prompt = f"""
You are an Investment Portfolio Analyst.

User Profile:

Name: {user['name']}
Age: {user['age']}
Income: ₹{user['income']}
Risk Profile: {risk}

Recommended Portfolio:

{portfolio}

Explain:

1. Why this portfolio suits the user
2. Benefits of the allocation
3. Risk vs Return tradeoff
4. One investment tip

Keep response under 120 words.
"""

        portfolio_explanation = ask_gemini(prompt)

        log_ai_usage(
            session["user_id"],
            "Portfolio Analyst"
        )

    except Exception as e:

        portfolio_explanation = f"""
AI Portfolio Analysis unavailable.

Error:
{str(e)}
"""

    return render_template(
        "portfolio.html",
        risk=risk,
        portfolio=portfolio,
        portfolio_explanation=portfolio_explanation
    )
@app.route(
    "/chatbot",
    methods=["GET", "POST"]
)
def chatbot():

    if "user_id" not in session:
        return redirect("/login")

    answer = None

    if request.method == "POST":

        question = request.form["question"]

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE id=%s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        cursor.execute(
            """
            SELECT SUM(amount) AS total
            FROM expenses
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        expense = float(
            cursor.fetchone()["total"] or 0
        )

        savings = float(user["income"]) - expense

        risk_type = session.get(
            "risk_type",
            "Not Assessed"
        )

        prompt = f"""
You are an expert AI Financial Advisor.

User Financial Profile:

Name: {user['name']}
Age: {user['age']}
Income: ₹{user['income']}
Total Expenses: ₹{expense}
Savings: ₹{savings}
Risk Profile: {risk_type}

User Question:
{question}

Provide:
1. Personalized advice
2. Practical recommendations
3. Clear financial reasoning

Keep the response concise and professional.
"""

        try:

            answer = ask_gemini(prompt)

            log_ai_usage(
                session["user_id"],
                "Financial Advisor"
            )

        except Exception as e:

            answer = f"""
AI Financial Advisor unavailable.

Error:
{str(e)}
"""

    return render_template(
        "chatbot.html",
        answer=answer
    )
@app.route("/goals", methods=["GET", "POST"])
def goals():

    if "user_id" not in session:
        return redirect("/login")

    monthly_saving = None
    goal_advice = None

    if request.method == "POST":

        goal_name = request.form["goal_name"]

        target_amount = float(
            request.form["target_amount"]
        )

        years = int(
            request.form["years"]
        )

        monthly_saving = round(
            target_amount / (years * 12),
            2
        )

        cursor.execute(
            """
            INSERT INTO goals
            (
                user_id,
                goal_name,
                target_amount,
                years
            )
            VALUES(%s,%s,%s,%s)
            """,
            (
                session["user_id"],
                goal_name,
                target_amount,
                years
            )
        )

        conn.commit()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE id=%s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        risk_type = session.get(
            "risk_type",
            "Not Assessed"
        )

        try:

            prompt = f"""
You are an expert Financial Planning Advisor.

User Details:

Name: {user['name']}
Age: {user['age']}
Income: ₹{user['income']}
Risk Profile: {risk_type}

Financial Goal:

Goal Name: {goal_name}
Target Amount: ₹{target_amount}
Time Horizon: {years} years
Required Monthly Saving: ₹{monthly_saving}

Provide:

1. Goal feasibility analysis
2. Savings recommendation
3. Investment suggestion
4. One actionable next step

Keep the response professional and under 120 words.
"""

            goal_advice = ask_gemini(prompt)

            log_ai_usage(
                session["user_id"],
                "Goal Advisor"
            )

        except Exception as e:

            goal_advice = f"""
AI Goal Advisor unavailable.

Error:
{str(e)}
"""

    cursor.execute(
        """
        SELECT *
        FROM goals
        WHERE user_id=%s
        ORDER BY id DESC
        """,
        (session["user_id"],)
    )

    goals = cursor.fetchall()

    return render_template(
        "goals.html",
        monthly_saving=monthly_saving,
        goal_advice=goal_advice,
        goals=goals
    )
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True) '''
from flask import Flask, render_template, request, session, redirect
from db import conn, cursor
import bcrypt
from portfolio_engine import get_portfolio
from dotenv import load_dotenv

load_dotenv()
from gemini_helper import ask_gemini
from sklearn.linear_model import LinearRegression
import numpy as np
from flask import send_file
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    PageBreak
)

from reportlab.lib import colors

import matplotlib.pyplot as plt

def log_ai_usage(user_id, feature):

    cursor.execute(
        """
        INSERT INTO ai_logs
        (
            user_id,
            feature_used
        )
        VALUES(%s,%s)
        """,
        (
            user_id,
            feature
        )
    )

    conn.commit()

app = Flask(__name__)
app.secret_key = "wealth_secret"
def generate_financial_insight(
    user,
    income,
    expense,
    savings,
    health_score,
    risk_type,
    forecast
):

    savings_rate = round(
        (savings / income) * 100
    ) if income > 0 else 0

    expense_rate = round(
        (expense / income) * 100
    ) if income > 0 else 0

    insight = f"""
Financial Overview

Your monthly income is Rs. {income:,.0f}
with total recorded expenses of
Rs. {expense:,.0f}.

Current savings amount to
Rs. {savings:,.0f},
representing approximately
{savings_rate}% of income.

Financial Health Analysis

Your financial health score is
{health_score}/100.

Expenses currently consume
{expense_rate}% of your income.

Risk Profile

Your investment profile is
classified as {risk_type}.

Future Outlook

Based on historical spending data,
the estimated next expense is
approximately Rs. {forecast if forecast else 'Not Available'}.

Recommendation

"""

    if health_score >= 70:

        insight += """
You are maintaining strong financial
discipline. Consider increasing
long-term investments and portfolio
diversification to maximize wealth
creation opportunities.
"""

    elif health_score >= 40:

        insight += """
Your finances remain stable but
there is room for improvement.

Reducing discretionary expenses
and increasing monthly investments
could significantly improve your
long-term financial position.
"""

    else:

        insight += """
Current spending patterns may
impact long-term financial goals.

Focus on improving savings habits,
budget planning and expense control.
"""

    return insight
def forecast_expense(user_id):

    cursor.execute(
        """
        SELECT amount
        FROM expenses
        WHERE user_id=%s
        ORDER BY expense_date
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    if len(rows) < 2:
        return None

    X = []
    y = []

    for i, row in enumerate(rows):

        X.append([i + 1])

        y.append(float(row["amount"]))

    model = LinearRegression()

    model.fit(X, y)

    next_month = [[len(rows) + 1]]

    prediction = model.predict(next_month)

    return round(float(prediction[0]), 2)

@app.route("/")
def home():
    return render_template("index.html")
@app.route("/report")
def report():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id=%s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    cursor.execute(
        """
        SELECT SUM(amount) AS total
        FROM expenses
        WHERE user_id=%s
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    expense = float(result["total"] or 0)

    savings = float(user["income"]) - expense

    if float(user["income"]) > 0:

        health_score = round(
            (savings / float(user["income"])) * 100
        )

    else:

        health_score = 0

    risk = session.get(
        "risk_type",
        "Not Assessed"
    )

    forecast = abs(
    forecast_expense(user_id)
) if forecast_expense(user_id) is not None else None

    cursor.execute(
        """
        SELECT *
        FROM goals
        WHERE user_id=%s
        ORDER BY id DESC
        """,
        (user_id,)
    )

    goals = cursor.fetchall()

    if risk == "Conservative":

        portfolio = {
            "Bonds": 50,
            "Mutual Funds": 25,
            "Stocks": 15,
            "Gold": 10
        }

    elif risk == "Moderate":

        portfolio = {
            "Stocks": 50,
            "Mutual Funds": 25,
            "Bonds": 15,
            "Gold": 10
        }

    else:

        portfolio = {
            "Stocks": 70,
            "Mutual Funds": 15,
            "Gold": 10,
            "Bonds": 5
        }

    pdf_file = "financial_report.pdf"

    doc = SimpleDocTemplate(pdf_file)

    styles = getSampleStyleSheet()

    elements = []
    elements.append(
    Paragraph(
        "WEALTH MANAGEMENT REPORT",
        styles["Title"]
    )
)

    elements.append(
    Paragraph(
        "AI Powered Personal Finance Analysis",
        styles["Heading3"]
    )
)

    elements.append(Spacer(1,20))
    elements.append(
    Paragraph(
        "Executive Summary",
        styles["Heading2"]
    )
)

    elements.append(
    Paragraph(
        f"""
This report analyzes the financial
position of {user['name']}.

Current savings amount to
Rs. {savings:,.0f} with a
Financial Health Score of
{health_score}/100.

Risk Profile:
{risk}
        """,
        styles["Normal"]
    )
)

    elements.append(
    Spacer(1,10)
)
    elements.append(Spacer(1, 12))

    elements.append(
        Paragraph(
            "User Profile",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            f"Name: {user['name']}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Age: {user['age']}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Income: Rs. {user['income']:,.0f}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Financial Summary",
            styles["Heading2"]
        )
    )
    if health_score >= 70:

        recommendation = """
Excellent financial discipline.

Continue investing regularly and
focus on portfolio diversification.
"""

    elif health_score >= 40:

        recommendation = """
    Moderate financial health.

    Increase monthly savings and
    review discretionary spending.
    """

    else:

        recommendation = """
    Financial health requires attention.

    Reduce expenses and establish
    a stronger savings habit.
    """
    elements.append(
        Paragraph(
            "Recommendations",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            recommendation,
            styles["Normal"]
        )
    )
    elements.append(
        Paragraph(
            f"Total Expenses: ₹{expense}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Savings: ₹{savings}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Health Score: {health_score}/100",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Risk Assessment",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            f"Risk Profile: {risk}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Portfolio Recommendation",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            "Recommended Allocation",
            styles["Heading3"]
        )
    )

    for asset,value in portfolio.items():

        elements.append(
            Paragraph(
                f"• {asset}: {value}%",
                styles["Normal"]
            )
        )
    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Machine Learning Forecast",
            styles["Heading2"]
        )
    )

    elements.append(
        Paragraph(
            f"Predicted Next Expense: ₹{forecast if forecast is not None else 'Not Available'}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            "Financial Goals",
            styles["Heading2"]
        )
    )

    if goals:

        for g in goals:

            elements.append(
                Paragraph(
                    f"{g['goal_name']} - ₹{g['target_amount']} ({g['years']} Years)",
                    styles["Normal"]
                )
            )

    else:

        elements.append(
            Paragraph(
                "No goals created yet.",
                styles["Normal"]
            )
        )
    cursor.execute(
        """
        SELECT category,
            SUM(amount) total
        FROM expenses
        WHERE user_id=%s
        GROUP BY category
        """,
        (user_id,)
    )

    expense_data = cursor.fetchall()

    if expense_data:

        labels = [
            row["category"]
            for row in expense_data
        ]

        values = [
            float(row["total"])
            for row in expense_data
        ]

        plt.figure(figsize=(5,5))

        plt.pie(
            values,
            labels=labels,
            autopct="%1.1f%%"
        )

        plt.title(
            "Expense Distribution"
        )

        chart_file = "expense_chart.png"

        plt.savefig(chart_file)

        plt.close()

        elements.append(
            PageBreak()
        )

        elements.append(
            Paragraph(
                "Expense Distribution",
                styles["Heading2"]
            )
        )

        elements.append(
            Image(
                chart_file,
                width=300,
                height=300
            )
        )
# ---------------- PORTFOLIO CHART ----------------

    portfolio_labels = list(
        portfolio.keys()
    )

    portfolio_values = list(
        portfolio.values()
    )

    plt.figure(figsize=(5,5))

    plt.pie(
        portfolio_values,
        labels=portfolio_labels,
        autopct="%1.1f%%"
    )

    plt.title(
        "Portfolio Allocation"
    )

    portfolio_chart = "portfolio_chart.png"

    plt.savefig(
        portfolio_chart
    )

    plt.close()

    elements.append(
        PageBreak()
    )

    elements.append(
        Paragraph(
            "Portfolio Allocation Analysis",
            styles["Heading2"]
        )
    )

    elements.append(
        Image(
            portfolio_chart,
            width=300,
            height=300
        )
    )
    doc.build(elements)

    return send_file(
        pdf_file,
        as_attachment=True
    )
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        age = request.form["age"]
        income = request.form["income"]

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email=%s
            """,
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            return "Email already registered. Please login."

        hashed_password = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        )

        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password,
                age,
                income
            )
            VALUES(%s,%s,%s,%s,%s)
            """,
            (
                name,
                email,
                hashed_password.decode(),
                age,
                income
            )
        )

        conn.commit()

        return redirect("/login")

    return render_template("register.html")
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        query = """
        SELECT * FROM users
        WHERE email=%s
        """

        cursor.execute(query,(email,))

        user = cursor.fetchone()

        if user:

            if bcrypt.checkpw(
                password.encode(),
                user["password"].encode()
            ):

                session["user_id"] = user["id"]

                return redirect("/dashboard")

        return "Invalid Credentials"

    return render_template("login.html")
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    # ---------------- USER DETAILS ----------------

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE id=%s
        """,
        (user_id,)
    )

    user = cursor.fetchone()

    # ---------------- TOTAL EXPENSES ----------------

    cursor.execute(
        """
        SELECT SUM(amount) AS total
        FROM expenses
        WHERE user_id=%s
        """,
        (user_id,)
    )

    result = cursor.fetchone()

    total_expense = float(
        result["total"] or 0
    )

    income = float(
        user["income"]
    )

    savings = income - total_expense

    # ---------------- HEALTH SCORE ----------------

    if income > 0:

        savings_ratio = savings / income

        health_score = max(
            0,
            min(
                100,
                round(savings_ratio * 100)
            )
        )

    else:

        health_score = 0
    

    if health_score < 40:

        recommendation = """
        Expenses are consuming a large
        percentage of income.

        Reduce discretionary spending
        and increase savings.
        """

    elif health_score < 70:

        recommendation = """
        Financial position is stable.

        Consider increasing investment
        contributions.
        """

    else:

        recommendation = """
        Strong financial health.

        Focus on wealth growth and
        portfolio diversification.
        """
    
    risk_type = session.get(
    "risk_type",
    "Not Assessed"
)

    forecast = forecast_expense(
    user_id
)

    if "dashboard_insight" in session:

        ai_insight = session[
        "dashboard_insight"
    ]

    else:

        ai_insight = generate_financial_insight(
        user,
        income,
        total_expense,
        savings,
        health_score,
        risk_type,
        forecast
    )

    session[
        "dashboard_insight"
    ] = ai_insight

    # ---------------- EXPENSE HISTORY ----------------

    cursor.execute(
        """
        SELECT *
        FROM expenses
        WHERE user_id=%s
        ORDER BY expense_date DESC
        """,
        (user_id,)
    )

    expenses = cursor.fetchall()

    # ---------------- CHART DATA ----------------

    cursor.execute(
        """
        SELECT
            category,
            SUM(amount) AS total
        FROM expenses
        WHERE user_id=%s
        GROUP BY category
        """,
        (user_id,)
    )

    chart_data = cursor.fetchall()

    # ---------------- ML FORECAST ----------------

    forecast = forecast_expense(
        user_id
    )

    return render_template(
        "dashboard.html",
        user=user,
        expense=total_expense,
        savings=savings,
        expenses=expenses,
        health_score=health_score,
        chart_data=chart_data,
        ai_insight=ai_insight,
        forecast=forecast
    )
@app.route("/expense", methods=["GET","POST"])
def expense():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        category = request.form["category"]

        amount = request.form["amount"]

        expense_date = request.form["expense_date"]

        query = """
        INSERT INTO expenses
        (
            user_id,
            category,
            amount,
            expense_date
        )
        VALUES(%s,%s,%s,%s)
        """

        cursor.execute(
            query,
            (
                session["user_id"],
                category,
                amount,
                expense_date
            )
        )

        conn.commit()
        session.pop(
    "dashboard_insight",
    None
)

        return redirect("/dashboard")

    return render_template("expense.html")
@app.route("/risk", methods=["GET", "POST"])
def risk():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        score = (
            int(request.form["q1"]) +
            int(request.form["q2"]) +
            int(request.form["q3"])
        )

        if score <= 4:
            risk_type = "Conservative"

        elif score <= 7:
            risk_type = "Moderate"

        else:
            risk_type = "Aggressive"

        cursor.execute(
            """
            INSERT INTO risk_profile
            (user_id, score, risk_type)
            VALUES (%s, %s, %s)
            """,
            (
                session["user_id"],
                score,
                risk_type
            )
        )

        conn.commit()

        # Allow access to portfolio only once
        session["risk_type"] = risk_type

        return redirect("/portfolio")

    return render_template("risk.html")
@app.route("/portfolio")
def portfolio():

    if "user_id" not in session:
        return redirect("/login")

    # If user refreshes page directly
    if "risk_type" not in session:
        return redirect("/risk")

    cursor.execute(
        """
        SELECT *
        FROM risk_profile
        WHERE user_id=%s
        ORDER BY id DESC
        LIMIT 1
        """,
        (session["user_id"],)
    )

    risk = cursor.fetchone()

    if not risk:
        return redirect("/risk")

    portfolio = get_portfolio(
        risk["risk_type"]
    )

    # ---------------------------
    # Gemini Portfolio Analysis
    # ---------------------------

    try:

        prompt = f"""
        User Risk Profile: {risk['risk_type']}

        Portfolio Allocation:
        {portfolio}

        Explain this portfolio in simple terms.

        Mention:
        - strengths
        - diversification
        - risk level
        - long term suitability
        - suggestions

        Keep the response concise.
        """

        response = model.generate_content(prompt)

        ai_analysis = response.text

    except Exception as e:

        print("Gemini Error:", e)

        ai_analysis = (
            "AI analysis is temporarily unavailable. "
            "Please try again later."
        )

    # Remove session key after opening portfolio
    session.pop("risk_type", None)

    return render_template(
        "portfolio.html",
        risk=risk["risk_type"],
        portfolio=portfolio,
        ai_analysis=ai_analysis
    )
@app.route(
    "/chatbot",
    methods=["GET", "POST"]
)
def chatbot():

    if "user_id" not in session:
        return redirect("/login")

    answer = None

    if request.method == "POST":

        question = request.form["question"]

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE id=%s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        cursor.execute(
            """
            SELECT SUM(amount) AS total
            FROM expenses
            WHERE user_id=%s
            """,
            (session["user_id"],)
        )

        expense = float(
            cursor.fetchone()["total"] or 0
        )

        savings = float(user["income"]) - expense

        risk_type = session.get(
            "risk_type",
            "Not Assessed"
        )

        prompt = f"""
You are an expert AI Financial Advisor.

User Financial Profile:

Name: {user['name']}
Age: {user['age']}
Income: ₹{user['income']}
Total Expenses: ₹{expense}
Savings: ₹{savings}
Risk Profile: {risk_type}

User Question:
{question}

Provide:
1. Personalized advice
2. Practical recommendations
3. Clear financial reasoning

Keep the response concise and professional.
"""

        try:

            answer = ask_gemini(prompt)

            log_ai_usage(
                session["user_id"],
                "Financial Advisor"
            )

        except Exception as e:

            answer = f"""
AI Financial Advisor unavailable.

Error:
{str(e)}
"""

    return render_template(
        "chatbot.html",
        answer=answer
    )
@app.route("/goals", methods=["GET", "POST"])
def goals():

    if "user_id" not in session:
        return redirect("/login")

    monthly_saving = None
    goal_advice = None

    if request.method == "POST":

        goal_name = request.form["goal_name"]

        target_amount = float(
            request.form["target_amount"]
        )

        years = int(
            request.form["years"]
        )

        monthly_saving = round(
            target_amount / (years * 12),
            2
        )

        cursor.execute(
            """
            INSERT INTO goals
            (
                user_id,
                goal_name,
                target_amount,
                years
            )
            VALUES(%s,%s,%s,%s)
            """,
            (
                session["user_id"],
                goal_name,
                target_amount,
                years
            )
        )

        conn.commit()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE id=%s
            """,
            (session["user_id"],)
        )

        user = cursor.fetchone()

        risk_type = session.get(
            "risk_type",
            "Not Assessed"
        )

        try:

            prompt = f"""
You are an expert Financial Planning Advisor.

User Details:

Name: {user['name']}
Age: {user['age']}
Income: ₹{user['income']}
Risk Profile: {risk_type}

Financial Goal:

Goal Name: {goal_name}
Target Amount: ₹{target_amount}
Time Horizon: {years} years
Required Monthly Saving: ₹{monthly_saving}

Provide:

1. Goal feasibility analysis
2. Savings recommendation
3. Investment suggestion
4. One actionable next step

Keep the response professional and under 120 words.
"""

            goal_advice = ask_gemini(prompt)

            log_ai_usage(
                session["user_id"],
                "Goal Advisor"
            )

        except Exception as e:

            goal_advice = f"""
AI Goal Advisor unavailable.

Error:
{str(e)}
"""

    cursor.execute(
        """
        SELECT *
        FROM goals
        WHERE user_id=%s
        ORDER BY id DESC
        """,
        (session["user_id"],)
    )

    goals = cursor.fetchall()

    return render_template(
        "goals.html",
        monthly_saving=monthly_saving,
        goal_advice=goal_advice,
        goals=goals
    )
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)