import streamlit as st

def show_about():
    st.markdown('<div class="main-header">About Us</div>', unsafe_allow_html=True)
    
    # Company overview
    st.markdown("""
    <div class="card">
        <h2>Our Mission</h2>
        <p>
            At Stock Analyzer, our mission is to democratize financial analysis and empower individual investors with professional-grade tools and insights. We believe that everyone should have access to sophisticated stock analysis capabilities, regardless of their experience level or portfolio size.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Company story
    st.markdown('<div class="sub-header">Our Story</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <p>
            Stock Analyzer was founded in 2023 by a team of finance professionals and software engineers who recognized a gap in the market for accessible, yet powerful stock analysis tools. Traditional financial analysis tools were either too complex for the average investor or too simplistic to provide meaningful insights.
        </p>
        <p>
            Our team set out to build a platform that combines sophisticated analysis capabilities with an intuitive user interface, making it accessible to investors of all levels. We've integrated cutting-edge technologies like machine learning and natural language processing to provide insights that were previously available only to institutional investors.
        </p>
        <p>
            Today, Stock Analyzer serves thousands of investors worldwide, helping them make more informed investment decisions and achieve their financial goals.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Team section
    st.markdown('<div class="sub-header">Our Team</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="team-card">
            <img src="app/images/photo.jpg" alt="John Smith" class="team-image">
            <h3>Jay Pawar</h3>
            <p class="team-title">CEO & Co-Founder</p>
            <p>Former investment banker with 15 years of experience in financial markets. MBA from Harvard Business School.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="team-card">
            <img src="" alt="Sarah Johnson" class="team-image">
            <h3>Alfaj Mulla</h3>
            <p class="team-title">CTO & Co-Founder</p>
            <p>AI and machine learning expert with a Ph.D. in Computer Science from MIT. Previously led engineering teams at major tech companies.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="team-card">
            <img src="" alt="Michael Chen" class="team-image">
            <h3>Akash Gurav</h3>
            <p class="team-title">Chief Data Scientist</p>
            <p>Quantitative analyst with expertise in statistical modeling and financial forecasting. Ph.D. in Financial Mathematics from Stanford.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="team-card">
            <img src="" alt="Michael Chen" class="team-image">
            <h3>Sanika Navale</h3>
            <p class="team-title">Chief Data Scientist</p>
            <p>Quantitative analyst with expertise in statistical modeling and financial forecasting. Ph.D. in Financial Mathematics from Stanford.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Company values
    st.markdown('<div class="sub-header">Our Values</div>', unsafe_allow_html=True)
    
    values = [
        {
            "title": "Accessibility",
            "description": "We believe financial analysis tools should be accessible to everyone, regardless of their experience or resources."
        },
        {
            "title": "Transparency",
            "description": "We are committed to transparency in our methodologies and data sources, ensuring users understand the basis of our analyses."
        },
        {
            "title": "Education",
            "description": "We are dedicated to educating our users, helping them become more knowledgeable and confident investors."
        },
        {
            "title": "Innovation",
            "description": "We continuously innovate and improve our platform, incorporating the latest technologies and methodologies."
        }
    ]
    
    cols = st.columns(2)
    
    for i, value in enumerate(values):
        col = cols[i % 2]
        
        with col:
            st.markdown(f"""
            <div class="value-card">
                <h3>{value['title']}</h3>
                <p>{value['description']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Contact information
    st.markdown('<div class="sub-header">Contact Us</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <p>
            We'd love to hear from you! Whether you have questions, feedback, or suggestions, please don't hesitate to reach out.
        </p>
        <p>
            <strong>Email:</strong> info@stockanalyzer.com<br>
            <strong>Phone:</strong> (123) 456-7890<br>
            <strong>Address:</strong> 123 Financial District, New York, NY 10004
        </p>
        <p>
            Follow us on social media:
            <a href="#" target="_blank">Twitter</a> |
            <a href="#" target="_blank">LinkedIn</a> |
            <a href="#" target="_blank">Facebook</a>
        </p>
    </div>
    """, unsafe_allow_html=True)
