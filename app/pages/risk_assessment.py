import streamlit as st
import sqlite3
from datetime import datetime

def show_risk_assessment(user_id):
    st.markdown('<div class="main-header">Risk Tolerance Assessment</div>', unsafe_allow_html=True)
    
    # Check if user already has a risk assessment
    conn = sqlite3.connect('database/stock_analyzer.db')
    c = conn.cursor()
    
    c.execute("""
    SELECT risk_score, risk_profile, risk_description, created_at
    FROM risk_assessments
    WHERE user_id = ?
    ORDER BY created_at DESC
    LIMIT 1
    """, (user_id,))
    
    risk_assessment = c.fetchone()
    conn.close()
    
    if risk_assessment:
        # Display current risk profile
        risk_score, risk_profile, description, assessment_date = risk_assessment
        
        st.markdown(f"""
        <div class="card">
            <h2>Your Risk Profile</h2>
            <h3>Risk Score: {risk_score:.1f}%</h3>
            <div class="progress-bar">
                <div class="progress" style="width: {risk_score}%;"></div>
            </div>
            <h3>Profile: {risk_profile}</h3>
            <p>{description}</p>
            <p class="small-text">Assessment date: {assessment_date}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Option to retake assessment
        if st.button("Retake Assessment"):
            assess_risk_tolerance(user_id)
    else:
        # Risk assessment questionnaire
        assess_risk_tolerance(user_id)

def assess_risk_tolerance(user_id):
    st.markdown('<div class="sub-header">Risk Tolerance Assessment</div>', unsafe_allow_html=True)
    st.write("Please answer the following questions to determine your risk tolerance level.")
    
    questions = [
        {
            "question": "How long do you plan to hold your investments?",
            "options": ["Less than 1 year", "1-3 years", "3-5 years", "5-10 years", "More than 10 years"],
            "weights": [1, 2, 3, 4, 5]
        },
        {
            "question": "How would you react if your portfolio lost 20% of its value in a month?",
            "options": ["Sell everything immediately", "Sell some investments", "Do nothing", "Buy a little more", "Buy significantly more"],
            "weights": [1, 2, 3, 4, 5]
        },
        {
            "question": "What is your primary investment goal?",
            "options": ["Preserve capital", "Generate income", "Balanced growth and income", "Growth", "Aggressive growth"],
            "weights": [1, 2, 3, 4, 5]
        },
        {
            "question": "What percentage of your total assets are you investing?",
            "options": ["Less than 10%", "10-25%", "25-50%", "50-75%", "More than 75%"],
            "weights": [5, 4, 3, 2, 1]
        },
        {
            "question": "How much investment experience do you have?",
            "options": ["None", "Limited", "Moderate", "Experienced", "Very experienced"],
            "weights": [1, 2, 3, 4, 5]
        }
    ]
    
    answers = []
    
    for i, q in enumerate(questions):
        st.write(f"**{i+1}. {q['question']}**")
        answer = st.radio(f"Question {i+1}", q['options'], key=f"q{i}", label_visibility="collapsed")
        answer_index = q['options'].index(answer)
        answers.append(q['weights'][answer_index])
    
    if st.button("Submit Assessment"):
        total_score = sum(answers)
        max_score = 5 * len(questions)
        risk_tolerance_pct = (total_score / max_score) * 100
        
        if risk_tolerance_pct < 30:
            risk_profile = "Conservative"
            description = "You prefer stability and are uncomfortable with significant market fluctuations. Focus on blue-chip stocks, dividend stocks, and consider bonds for stability."
        elif risk_tolerance_pct < 50:
            risk_profile = "Moderately Conservative"
            description = "You can tolerate some market volatility but prioritize capital preservation. Consider a mix of stable blue-chip stocks and some growth opportunities."
        elif risk_tolerance_pct < 70:
            risk_profile = "Moderate"
            description = "You have a balanced approach to risk and return. A diversified portfolio across sectors with a mix of value and growth stocks may be suitable."
        elif risk_tolerance_pct < 85:
            risk_profile = "Moderately Aggressive"
            description = "You're comfortable with significant market volatility for potential higher returns. Consider growth stocks, emerging markets, and some higher-risk sectors."
        else:
            risk_profile = "Aggressive"
            description = "You can tolerate high volatility for potentially high returns. Growth stocks, small caps, and emerging technologies may align with your risk tolerance."
        
        # Save to database
        conn = sqlite3.connect('database/stock_analyzer.db')
        c = conn.cursor()
        
        c.execute("""
        INSERT INTO risk_assessments (user_id, risk_score, risk_profile, risk_description, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        """, (user_id, risk_tolerance_pct, risk_profile, description))
        
        conn.commit()
        conn.close()
        
        st.success("Risk assessment completed!")
        st.rerun()
