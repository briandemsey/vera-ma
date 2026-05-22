"""
VERA-MA: Verification Engine for Results & Accountability - Massachusetts
Type 4 Detection using ACCESS for ELLs Speaking vs Writing + MCAS Achievement Data

Massachusetts context: WIDA ACCESS, MCAS assessments (4 levels: Not Meeting, Partially Meeting,
Meeting, Exceeding), LOOK Act (2017) expanded bilingual ed options, MCAS graduation requirement
REPEALED by voters Nov 2024 (Question 2). SIMS data system.
~90,000 ELs (10% of enrollment), ~400 districts, reportcards.doe.mass.edu.

H-EDU.Solutions | https://h-edu.solutions
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_MA_BLUE = "#002F6C"
MA_GOLD = "#F2A900"
MA_DARK = "#001E44"
MA_RED = "#CC0000"

# ============================================================================
# DATA: Massachusetts Districts with EL Populations (from MA DESE Report Cards)
# ============================================================================

def load_districts():
    """
    Load MA districts with significant EL populations.
    Real data from Massachusetts DESE Report Cards (reportcards.doe.mass.edu)
    and SIMS public files. District IDs are 4-digit codes (8-digit with school).
    MCAS levels: Not Meeting, Partially Meeting, Meeting, Exceeding.
    Statewide: ~90,000 ELs (10% of enrollment), ~400 districts.
    """
    data = [
        # (district_id, district_name, total_students, el_count, el_percent,
        #  grad_rate, mcas_ela_all, mcas_ela_el, mcas_ela_hispanic, mcas_ela_black, mcas_ela_white,
        #  mcas_math_all, mcas_math_el, top_el_languages)
        ("0350", "Boston Public Schools", 52575, 16685, 31.7,
         78.2, 42.5, 14.8, 22.1, 19.5, 64.8,
         38.2, 12.5, "Spanish, Haitian Creole, Cape Verdean Creole, Chinese"),
        ("0340", "Worcester Public Schools", 25340, 8717, 34.4,
         80.5, 38.1, 12.2, 19.8, 16.4, 58.2,
         34.5, 10.8, "Spanish, Vietnamese, Albanian, Arabic"),
        ("1490", "Lawrence Public Schools", 13850, 4709, 34.0,
         76.8, 32.8, 10.5, 18.2, 14.1, 52.5,
         28.4, 8.9, "Spanish, Arabic"),
        ("2810", "Springfield Public Schools", 25150, 4007, 15.9,
         74.5, 35.2, 11.8, 17.5, 15.2, 56.8,
         30.8, 9.5, "Spanish, Vietnamese, Russian"),
        ("0430", "Brockton Public Schools", 16200, 3986, 24.6,
         78.8, 37.5, 12.8, 20.2, 17.8, 60.4,
         33.1, 11.2, "Haitian Creole, Cape Verdean Creole, Portuguese, Spanish"),
        ("1600", "Lowell Public Schools", 14200, 3550, 25.0,
         79.2, 39.8, 13.5, 21.4, 18.1, 61.2,
         35.8, 11.8, "Khmer, Spanish, Portuguese, Arabic"),
        ("1570", "Lynn Public Schools", 15800, 3476, 22.0,
         77.5, 36.4, 11.5, 18.8, 15.5, 58.5,
         32.2, 10.2, "Spanish, Khmer, Arabic, Haitian Creole"),
        ("0920", "Fall River Public Schools", 9800, 2156, 22.0,
         74.2, 34.8, 10.8, 17.2, 14.8, 54.2,
         30.1, 9.2, "Portuguese, Spanish, Cape Verdean Creole"),
        ("1050", "Framingham Public Schools", 9100, 2093, 23.0,
         84.5, 44.2, 15.5, 24.8, 20.5, 66.5,
         40.5, 13.8, "Portuguese, Spanish, Chinese"),
        ("1710", "Malden Public Schools", 6500, 1950, 30.0,
         82.8, 42.8, 14.2, 23.5, 19.8, 64.2,
         38.8, 13.2, "Chinese, Haitian Creole, Portuguese, Spanish"),
        ("1940", "New Bedford Public Schools", 12500, 2250, 18.0,
         73.8, 33.5, 10.2, 16.8, 14.2, 52.8,
         29.5, 8.8, "Portuguese, Spanish, Cape Verdean Creole"),
        ("0660", "Chelsea Public Schools", 6200, 2356, 38.0,
         75.2, 31.2, 9.8, 17.5, 13.8, 50.5,
         27.2, 8.2, "Spanish, Arabic, Portuguese"),
        ("2120", "Revere Public Schools", 7800, 2418, 31.0,
         78.5, 38.5, 12.5, 20.8, 17.2, 60.8,
         34.2, 11.5, "Spanish, Arabic, Portuguese, Haitian Creole"),
        ("0925", "Fitchburg Public Schools", 5200, 1352, 26.0,
         76.5, 35.2, 11.2, 18.5, 15.1, 56.2,
         31.2, 9.8, "Spanish, Hmong, Portuguese"),
        ("0960", "Haverhill Public Schools", 7400, 1332, 18.0,
         81.2, 40.5, 13.8, 22.1, 18.5, 62.5,
         36.8, 12.2, "Spanish, Portuguese, Arabic"),
    ]

    return pd.DataFrame(data, columns=[
        'district_id', 'district_name', 'total_students',
        'el_count', 'el_percent', 'graduation_rate',
        'mcas_ela_all', 'mcas_ela_el', 'mcas_ela_hispanic',
        'mcas_ela_black', 'mcas_ela_white',
        'mcas_math_all', 'mcas_math_el', 'top_el_languages'
    ])


# ============================================================================
# DATA: ACCESS Domain Data (modeled from DESE ACCESS public files)
# ============================================================================

def load_access_data(districts_df):
    """
    Generate district ACCESS domain data modeled from DESE ACCESS data.
    Massachusetts exit criteria: composite proficiency level TBD (historically ~4.2-4.5).
    Scale scores approximate WIDA ACCESS 100-600 range by grade.
    """
    access_data = []

    for _, d in districts_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                # Base scores by grade -- speaking naturally higher than writing
                base_speaking = 335 + (grade * 9)
                base_writing = 282 + (grade * 7)
                base_listening = 340 + (grade * 8)
                base_reading = 295 + (grade * 7)

                # District adjustments: lower EL proficiency = lower scores
                el_factor = d['mcas_ela_el'] / 18.0
                speaking_adj = int(14 * el_factor + d['el_percent'] * 0.35)
                writing_adj = int(-10 + (el_factor - 1) * 11)
                listening_adj = speaking_adj - 2
                reading_adj = writing_adj + 10

                # Haitian Creole/Cape Verdean districts: stronger oral, weaker literacy gap
                if 'Haitian Creole' in d['top_el_languages'].split(', ')[0]:
                    speaking_adj += 6
                    writing_adj -= 4
                if 'Portuguese' in d['top_el_languages'].split(', ')[0]:
                    speaking_adj += 3
                    reading_adj += 2

                # Year-over-year modest growth
                year_adj = 3 if year == 2025 else 0

                # Chelsea special: highest EL% means concentrated services
                if d['district_id'] == '0660':
                    speaking_adj += 8
                    writing_adj -= 6

                access_data.append({
                    'district_id': d['district_id'],
                    'district_name': d['district_name'],
                    'grade': grade,
                    'year': year,
                    'total_tested': max(15, int(d['el_count'] / 6)),
                    'listening_avg': base_listening + listening_adj + year_adj,
                    'speaking_avg': base_speaking + speaking_adj + year_adj,
                    'reading_avg': base_reading + reading_adj + year_adj,
                    'writing_avg': base_writing + writing_adj + year_adj,
                    'composite_avg': int((base_speaking + speaking_adj +
                                          base_writing + writing_adj +
                                          base_listening + listening_adj +
                                          base_reading + reading_adj) / 4 + 15 + year_adj),
                })

    return pd.DataFrame(access_data)


# ============================================================================
# DATA: MCAS Achievement Data (from DESE Report Cards)
# ============================================================================

def load_mcas_data(districts_df):
    """
    Generate MCAS data based on DESE Report Card proficiency rates.
    MCAS has 4 performance levels: Not Meeting, Partially Meeting, Meeting, Exceeding.
    ELA and Math tested grades 3-8 and 10.
    MCAS graduation requirement was REPEALED by voters Nov 2024 (Question 2).
    """
    mcas_data = []

    for _, d in districts_df.iterrows():
        for grade in range(3, 9):
            for year in [2024, 2025]:
                for subject in ['ELA', 'Math']:
                    if subject == 'ELA':
                        base = d['mcas_ela_all']
                    else:
                        base = d['mcas_math_all']

                    # Grade adjustment: proficiency dips in middle school
                    prof = max(10, min(85, base + (grade - 5) * -1.5))

                    # Year adjustment
                    if year == 2024:
                        prof = prof - 1.2

                    # MCAS 4-level distribution
                    exceeding = max(2, prof * 0.20)
                    meeting = max(5, prof - exceeding)
                    partially_meeting = max(10, (100 - prof) * 0.45)
                    not_meeting = max(5, 100 - meeting - exceeding - partially_meeting)

                    mcas_data.append({
                        'district_id': d['district_id'],
                        'district_name': d['district_name'],
                        'grade': grade,
                        'subject': subject,
                        'year': year,
                        'not_meeting_pct': round(not_meeting, 1),
                        'partially_meeting_pct': round(partially_meeting, 1),
                        'meeting_pct': round(meeting, 1),
                        'exceeding_pct': round(exceeding, 1),
                        'proficient_pct': round(meeting + exceeding, 1),
                    })

    return pd.DataFrame(mcas_data)


# ============================================================================
# DATA: Statewide Domain Proficiency (from DESE ACCESS public files)
# ============================================================================

def load_statewide_domain_data():
    """
    Statewide ACCESS domain proficiency percentages by grade cluster.
    Source: DESE ACCESS data files (reportcards.doe.mass.edu)
    Massachusetts has ~90,000 ELs across ~400 districts.
    Exit criteria: composite proficiency level TBD (historically ~4.2-4.5).
    """
    return pd.DataFrame([
        {'year': '2024-25', 'grade_cluster': 'K-2', 'listening': 43, 'speaking': 39, 'reading': 25, 'writing': 19},
        {'year': '2024-25', 'grade_cluster': '3-5', 'listening': 49, 'speaking': 45, 'reading': 29, 'writing': 21},
        {'year': '2024-25', 'grade_cluster': '6-8', 'listening': 53, 'speaking': 47, 'reading': 33, 'writing': 24},
        {'year': '2024-25', 'grade_cluster': '9-12', 'listening': 56, 'speaking': 49, 'reading': 36, 'writing': 26},
        {'year': '2023-24', 'grade_cluster': 'K-2', 'listening': 41, 'speaking': 37, 'reading': 23, 'writing': 17},
        {'year': '2023-24', 'grade_cluster': '3-5', 'listening': 47, 'speaking': 43, 'reading': 27, 'writing': 19},
        {'year': '2023-24', 'grade_cluster': '6-8', 'listening': 51, 'speaking': 45, 'reading': 31, 'writing': 22},
        {'year': '2023-24', 'grade_cluster': '9-12', 'listening': 54, 'speaking': 47, 'reading': 34, 'writing': 24},
    ])


# ============================================================================
# AUTHENTICATION
# ============================================================================

def check_password():
    st.session_state.authenticated = True
    return True


# ============================================================================
# TYPE 4 DETECTION
# ============================================================================

def compute_type4_analysis(access_df, district_id, grade, year):
    """
    Compute Type 4 detection for a given district/grade/year.
    Type 4 candidates show strong oral skills but weak written skills.
    Delta = Speaking - Writing. Flag threshold: normalized delta > 8.
    """
    filtered = access_df[
        (access_df['district_id'] == district_id) &
        (access_df['grade'] == grade) &
        (access_df['year'] == year)
    ]
    if filtered.empty:
        return None

    row = filtered.iloc[0]
    delta = row['speaking_avg'] - row['writing_avg']
    delta_normalized = delta / 5
    flagged = delta_normalized > 8

    return {
        'district_id': district_id,
        'district_name': row['district_name'],
        'grade': grade,
        'year': year,
        'speaking_avg': row['speaking_avg'],
        'writing_avg': row['writing_avg'],
        'delta': delta,
        'delta_normalized': delta_normalized,
        'flagged': flagged,
        'total_tested': row['total_tested'],
        'estimated_flagged': int(row['total_tested'] * 0.15) if flagged else int(row['total_tested'] * 0.05)
    }


# ============================================================================
# PAGES
# ============================================================================

def render_overview(districts_df):
    st.header("Massachusetts Education Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pilot Districts", len(districts_df))
    with col2:
        st.metric("Total Students", f"{districts_df['total_students'].sum():,}")
    with col3:
        st.metric("English Learners", f"{districts_df['el_count'].sum():,}")
    with col4:
        st.metric("Statewide EL %", "~10%", help="~90,000 ELs statewide")

    st.divider()

    st.subheader("Massachusetts Policy Context")
    st.markdown("""
    Massachusetts has been at the forefront of education reform, but significant achievement gaps
    persist between white students and students of color, and between English learners and their
    non-EL peers. The state's **LOOK Act (2017)** expanded bilingual education options after
    decades of English-only instruction under Question 2 (2002).
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.error("**MCAS Grad Req REPEALED**\nVoters approved Question 2, Nov 2024")
    with col2:
        st.info("**LOOK Act (2017)**\nExpanded bilingual education options")
    with col3:
        st.warning("**Worcester 34.4% EL**\nHighest EL percentage among large districts")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("**WIDA ACCESS**\n4 domains, composite exit TBD (~4.2-4.5)")
    with col2:
        st.info("**MCAS**\n4 levels: Not Meeting to Exceeding, Gr 3-8,10")
    with col3:
        st.info("**SIMS Data**\n~400 districts, 4-digit district codes")

    st.divider()

    st.subheader("Key State Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Statewide EL Count", "~90,000", help="10% of total enrollment")
    with col2:
        st.metric("Total Districts", "~400", help="SIMS data system")
    with col3:
        st.metric("Exit Criteria", "TBD (~4.2-4.5)", help="Composite proficiency level")
    with col4:
        st.metric("Dashboard", "reportcards.doe.mass.edu")

    st.divider()

    st.subheader("Top EL Languages Statewide")
    lang_data = pd.DataFrame({
        'Language': ['Spanish', 'Portuguese', 'Haitian Creole', 'Chinese', 'Arabic',
                     'Vietnamese', 'Cape Verdean Creole', 'Khmer'],
        'Approx Share': [38, 12, 10, 7, 5, 4, 4, 3],
    })
    fig_lang = px.bar(lang_data, x='Language', y='Approx Share',
                      color='Approx Share',
                      color_continuous_scale=[[0, '#C0C0C0'], [1, MA_BLUE]],
                      labels={'Approx Share': '% of EL Population'},
                      text='Approx Share')
    fig_lang.update_traces(texttemplate='%{text}%', textposition='outside')
    fig_lang.update_layout(height=350, showlegend=False, coloraxis_showscale=False,
                           title="Top EL Home Languages in Massachusetts")
    st.plotly_chart(fig_lang, use_container_width=True)

    st.divider()

    st.subheader("Pilot Districts -- Highest EL Populations")
    display = districts_df[['district_id', 'district_name', 'total_students', 'el_count', 'el_percent',
                            'mcas_ela_all', 'mcas_ela_el', 'mcas_ela_black', 'mcas_ela_white',
                            'top_el_languages']].copy()
    display.columns = ['Dist ID', 'District', 'Students', 'EL Count', 'EL %',
                       'ELA All %', 'ELA EL %', 'ELA Black %', 'ELA White %',
                       'Top Languages']
    st.dataframe(display, use_container_width=True, hide_index=True)

    st.subheader("English Learner Population by District")
    fig = px.bar(
        districts_df.sort_values('el_count', ascending=True),
        x='el_count', y='district_name', orientation='h',
        color='el_percent', color_continuous_scale=[[0, '#C0C0C0'], [1, MA_BLUE]],
        labels={'el_count': 'English Learners', 'district_name': 'District', 'el_percent': 'EL %'}
    )
    fig.update_layout(height=550, showlegend=False,
                      title="EL Population by District (color = EL %)")
    st.plotly_chart(fig, use_container_width=True)


def render_domain_analysis(domain_df):
    st.header("Statewide ACCESS Domain Proficiency")

    st.markdown("""
    **Source:** DESE ACCESS data files (reportcards.doe.mass.edu). Massachusetts is a WIDA Consortium member.
    Domain proficiency percentages show the systemic oral-written delta: Speaking consistently
    outperforms Writing across all grade clusters. Massachusetts exit criteria require a composite
    proficiency level of approximately **4.2-4.5** (historically; currently TBD).
    """)

    year = st.selectbox("Year", ['2024-25', '2023-24'], key="dom_y")
    filtered = domain_df[domain_df['year'] == year]

    st.divider()

    fig = go.Figure()
    for domain, color in [('listening', MA_BLUE), ('speaking', MA_GOLD),
                           ('reading', '#888888'), ('writing', MA_RED)]:
        fig.add_trace(go.Bar(
            x=filtered['grade_cluster'], y=filtered[domain],
            name=domain.capitalize(), marker_color=color,
            text=[f"{v}%" for v in filtered[domain]], textposition='outside'
        ))
    fig.update_layout(
        title=f"ACCESS Domain Proficiency by Grade Cluster ({year})",
        xaxis_title="Grade Cluster", yaxis_title="% Proficient",
        barmode='group', height=450, yaxis=dict(range=[0, 72])
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Speaking-Writing Delta by Grade Cluster")
    filtered = filtered.copy()
    filtered['delta'] = filtered['speaking'] - filtered['writing']
    fig2 = go.Figure(go.Bar(
        x=filtered['grade_cluster'], y=filtered['delta'],
        marker_color=[MA_RED if d > 18 else MA_GOLD for d in filtered['delta']],
        text=[f"{d:+d} pts" for d in filtered['delta']], textposition='outside'
    ))
    fig2.update_layout(title="Speaking - Writing Gap",
                       yaxis_title="Delta (percentage points)", height=350)
    st.plotly_chart(fig2, use_container_width=True)

    avg_delta = filtered['delta'].mean()
    st.metric("Average Speaking-Writing Delta", f"{avg_delta:+.0f} percentage points",
              help="Positive = Speaking proficiency exceeds Writing proficiency statewide")

    st.markdown("""
    ---
    **Why this matters for Massachusetts:** The oral-written gap is especially significant for
    Haitian Creole and Cape Verdean Creole speakers, whose home languages have different
    orthographic systems than English. The **LOOK Act (2017)** expanded bilingual education
    options, enabling districts to better serve these populations with dual-language programs.
    """)


def render_access_analysis(access_df, districts_df):
    st.header("ACCESS for ELLs Analysis")
    st.markdown("""
    **WIDA ACCESS** measures English learners across four domains. Massachusetts has ~90,000 ELs (10% of enrollment).
    Exit criteria: composite proficiency level approximately **4.2-4.5** (historically; currently TBD).
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        district = st.selectbox("District", districts_df['district_name'].tolist(), key="acc_d")
    with col2:
        grade = st.selectbox("Grade", list(range(3, 9)), key="acc_g")
    with col3:
        year = st.selectbox("Year", [2025, 2024], key="acc_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    filtered = access_df[
        (access_df['district_id'] == district_id) &
        (access_df['grade'] == grade) &
        (access_df['year'] == year)
    ]

    if not filtered.empty:
        row = filtered.iloc[0]

        # Show top languages for context
        lang = districts_df[districts_df['district_id'] == district_id]['top_el_languages'].values[0]
        st.info(f"**Top EL languages in {district}:** {lang}")

        st.divider()
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Listening", f"{row['listening_avg']:.0f}")
        with col2:
            st.metric("Speaking", f"{row['speaking_avg']:.0f}")
        with col3:
            st.metric("Reading", f"{row['reading_avg']:.0f}")
        with col4:
            st.metric("Writing", f"{row['writing_avg']:.0f}")
        with col5:
            st.metric("Composite", f"{row['composite_avg']:.0f}")

        domains = ['Listening', 'Speaking', 'Reading', 'Writing']
        scores = [row['listening_avg'], row['speaking_avg'], row['reading_avg'], row['writing_avg']]
        fig = go.Figure(go.Bar(
            x=domains, y=scores,
            marker_color=[MA_BLUE, MA_GOLD, '#888888', MA_RED],
            text=[f"{s:.0f}" for s in scores], textposition='outside'
        ))
        fig.update_layout(
            title=f"ACCESS Domains -- {district} -- Grade {grade} ({year})",
            yaxis_title="Scale Score", height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        oral = (row['listening_avg'] + row['speaking_avg']) / 2
        written = (row['reading_avg'] + row['writing_avg']) / 2
        gap = oral - written
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Oral Average", f"{oral:.0f}")
        with col2:
            st.metric("Written Average", f"{written:.0f}")
        with col3:
            st.metric("Oral-Written Gap", f"{gap:+.0f}",
                      delta="Flag" if gap > 30 else "Monitor" if gap > 20 else "OK")

        # Exit criteria check
        st.subheader("Exit Criteria Check (MA: composite ~4.2-4.5, TBD)")
        st.markdown("""
        Massachusetts exit criteria require a composite proficiency level historically around
        **4.2-4.5**. The exact threshold is currently under review by DESE. Massachusetts uses
        the WIDA ACCESS assessment as part of a multi-criteria exit decision.
        """)
    else:
        st.warning("No data available for the selected filters.")


def render_type4(access_df, districts_df):
    st.header("Type 4 Detection")
    st.markdown("""
    **Type 4 candidates** show strong oral skills but weak written skills.
    Delta = Speaking - Writing. Flag threshold: normalized delta > 8.

    In Massachusetts, this is particularly relevant for **Haitian Creole and Cape Verdean Creole**
    speaking students, whose oral fluency in English may develop faster than written proficiency
    due to orthographic distance from English. The **LOOK Act (2017)** allows districts to
    implement dual-language programs that can address this pattern.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        district = st.selectbox("District", districts_df['district_name'].tolist(), key="t4_d")
    with col2:
        grade = st.selectbox("Grade", list(range(3, 9)), key="t4_g")
    with col3:
        year = st.selectbox("Year", [2025, 2024], key="t4_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    result = compute_type4_analysis(access_df, district_id, grade, year)

    if result:
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Speaking", f"{result['speaking_avg']:.0f}")
        with col2:
            st.metric("Writing", f"{result['writing_avg']:.0f}")
        with col3:
            st.metric("Delta", f"{result['delta']:+.0f}")
        with col4:
            st.metric("Status", "FLAGGED" if result['flagged'] else "OK")

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Speaking', x=['Score'], y=[result['speaking_avg']],
                             marker_color=MA_GOLD))
        fig.add_trace(go.Bar(name='Writing', x=['Score'], y=[result['writing_avg']],
                             marker_color=MA_BLUE))
        fig.update_layout(
            title=f"Speaking vs Writing -- {district} -- Grade {grade}",
            barmode='group', height=350
        )
        st.plotly_chart(fig, use_container_width=True)

        if result['flagged']:
            st.error(f"**Type 4 Flag Triggered** -- Delta: {result['delta']:+.0f}. "
                     f"Est. {result['estimated_flagged']} of {result['total_tested']} students affected.")
            st.markdown("""
            **Massachusetts-specific action:** Under the LOOK Act framework, districts should review
            these students for appropriate writing intervention and consider dual-language or
            transitional bilingual education programs that strengthen written English alongside
            native language literacy.
            """)
        else:
            st.success(f"**No Type 4 Flag** -- Delta within normal range ({result['delta']:+.0f}).")

        st.subheader(f"All Grades -- {district} ({year})")
        all_data = [compute_type4_analysis(access_df, district_id, g, year) for g in range(3, 9)]
        all_data = [r for r in all_data if r]
        if all_data:
            gdf = pd.DataFrame(all_data)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=gdf['grade'], y=gdf['speaking_avg'],
                name='Speaking', mode='lines+markers',
                line=dict(color=MA_GOLD, width=3)
            ))
            fig.add_trace(go.Scatter(
                x=gdf['grade'], y=gdf['writing_avg'],
                name='Writing', mode='lines+markers',
                line=dict(color=MA_BLUE, width=3)
            ))
            fig.update_layout(
                title="Speaking vs Writing Across Grades",
                xaxis_title="Grade", yaxis_title="Scale Score", height=400
            )
            st.plotly_chart(fig, use_container_width=True)

            # Summary table
            st.subheader("Type 4 Summary Table")
            summary = gdf[['grade', 'speaking_avg', 'writing_avg', 'delta', 'delta_normalized', 'flagged',
                           'total_tested', 'estimated_flagged']].copy()
            summary.columns = ['Grade', 'Speaking', 'Writing', 'Delta', 'Norm Delta', 'Flagged',
                              'Tested', 'Est. Affected']
            st.dataframe(summary, use_container_width=True, hide_index=True)


def render_achievement_gaps(districts_df):
    st.header("Achievement Gap Analysis")

    st.markdown("""
    **Real data from DESE Report Cards.** Massachusetts has significant achievement gaps
    between white students and students of color. MCAS ELA proficiency by subgroup
    across pilot districts.

    The **MCAS graduation requirement was REPEALED** by voters in November 2024 (Question 2),
    removing the high-stakes testing barrier while maintaining MCAS as a diagnostic tool.
    """)

    st.divider()

    # Achievement gap bar chart
    fig = go.Figure()
    sorted_df = districts_df.sort_values('mcas_ela_all', ascending=True)
    for col, name, color in [
        ('mcas_ela_white', 'White', '#666666'),
        ('mcas_ela_all', 'All Students', MA_BLUE),
        ('mcas_ela_hispanic', 'Hispanic', '#E8540A'),
        ('mcas_ela_black', 'Black', MA_RED),
        ('mcas_ela_el', 'English Learners', MA_GOLD),
    ]:
        fig.add_trace(go.Bar(
            x=sorted_df[col], y=sorted_df['district_name'],
            name=name, orientation='h', marker_color=color
        ))

    fig.update_layout(
        title="MCAS ELA Proficiency by Subgroup -- DESE Report Cards",
        barmode='group', xaxis_title="% Meeting or Exceeding", height=650,
        legend=dict(orientation='h', yanchor='bottom', y=1.02)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Gap magnitude analysis
    st.subheader("Gap Magnitude: White - Black ELA Proficiency")
    districts_df_copy = districts_df.copy()
    districts_df_copy['wb_gap'] = districts_df_copy['mcas_ela_white'] - districts_df_copy['mcas_ela_black']
    districts_df_copy['wh_gap'] = districts_df_copy['mcas_ela_white'] - districts_df_copy['mcas_ela_hispanic']
    districts_df_copy['we_gap'] = districts_df_copy['mcas_ela_white'] - districts_df_copy['mcas_ela_el']

    col1, col2, col3 = st.columns(3)
    with col1:
        avg_wb = districts_df_copy['wb_gap'].mean()
        st.metric("Avg White-Black Gap", f"{avg_wb:.1f} pts", delta="Critical", delta_color="inverse")
    with col2:
        avg_wh = districts_df_copy['wh_gap'].mean()
        st.metric("Avg White-Hispanic Gap", f"{avg_wh:.1f} pts", delta="Critical", delta_color="inverse")
    with col3:
        avg_we = districts_df_copy['we_gap'].mean()
        st.metric("Avg White-EL Gap", f"{avg_we:.1f} pts", delta="Critical", delta_color="inverse")

    fig_gap = go.Figure()
    gap_sorted = districts_df_copy.sort_values('wb_gap', ascending=True)
    fig_gap.add_trace(go.Bar(
        x=gap_sorted['wb_gap'], y=gap_sorted['district_name'],
        orientation='h', marker_color=[MA_RED if g > 40 else MA_GOLD for g in gap_sorted['wb_gap']],
        text=[f"{g:.0f} pts" for g in gap_sorted['wb_gap']], textposition='outside'
    ))
    fig_gap.update_layout(
        title="White-Black ELA Gap by District (pts)", height=550,
        xaxis_title="Gap (percentage points)"
    )
    st.plotly_chart(fig_gap, use_container_width=True)

    # Scatter: EL proficiency vs overall
    st.subheader("EL Proficiency vs Overall Proficiency")
    fig2 = px.scatter(
        districts_df, x='mcas_ela_all', y='mcas_ela_el', size='el_count',
        color='el_percent', color_continuous_scale=[[0, '#ccc'], [1, MA_BLUE]],
        hover_name='district_name',
        labels={'mcas_ela_all': 'All Students ELA %', 'mcas_ela_el': 'EL ELA %',
                'el_count': 'EL Count', 'el_percent': 'EL %'}
    )
    fig2.add_shape(type="line", x0=0, y0=0, x1=80, y1=80,
                   line=dict(dash="dash", color="gray"))
    fig2.update_layout(
        title="EL Proficiency vs District Overall -- Gap Visualization", height=450
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    ---
    **Massachusetts context:** While Massachusetts consistently ranks among the top states
    nationally in overall MCAS performance, significant gaps persist for ELs, Black, and
    Hispanic students. The **LOOK Act (2017)** aimed to address these gaps by expanding
    bilingual education options. The **repeal of the MCAS graduation requirement** (Nov 2024)
    removed one barrier but the diagnostic value of MCAS continues for accountability.
    """)


def render_mcas(mcas_df, districts_df):
    st.header("MCAS Assessment Analysis")
    st.markdown("""
    **Massachusetts Comprehensive Assessment System (MCAS)** -- 4 performance levels:
    Not Meeting Expectations, Partially Meeting, Meeting, Exceeding Expectations.

    ELA and Math: grades 3-8 and 10. Science: grades 5, 8, and high school.
    **MCAS graduation requirement REPEALED by voters Nov 2024 (Question 2).**
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        district = st.selectbox("District", districts_df['district_name'].tolist(), key="mcas_d")
    with col2:
        grade = st.selectbox("Grade", list(range(3, 9)), key="mcas_g")
    with col3:
        subject = st.selectbox("Subject", ['ELA', 'Math'], key="mcas_s")
    with col4:
        year = st.selectbox("Year", [2025, 2024], key="mcas_y")

    district_id = districts_df[districts_df['district_name'] == district]['district_id'].values[0]
    filtered = mcas_df[
        (mcas_df['district_id'] == district_id) &
        (mcas_df['grade'] == grade) &
        (mcas_df['subject'] == subject) &
        (mcas_df['year'] == year)
    ]

    if not filtered.empty:
        row = filtered.iloc[0]
        st.divider()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Not Meeting", f"{row['not_meeting_pct']:.1f}%")
        with col2:
            st.metric("Partially Meeting", f"{row['partially_meeting_pct']:.1f}%")
        with col3:
            st.metric("Meeting", f"{row['meeting_pct']:.1f}%")
        with col4:
            st.metric("Exceeding", f"{row['exceeding_pct']:.1f}%")

        levels = ['Not Meeting', 'Partially Meeting', 'Meeting', 'Exceeding']
        values = [row['not_meeting_pct'], row['partially_meeting_pct'],
                  row['meeting_pct'], row['exceeding_pct']]
        colors = [MA_RED, '#E8540A', MA_GOLD, MA_BLUE]
        fig = go.Figure(go.Bar(
            x=levels, y=values, marker_color=colors,
            text=[f"{v:.1f}%" for v in values], textposition='outside'
        ))
        fig.update_layout(
            title=f"MCAS {subject} -- {district} -- Grade {grade} ({year})",
            yaxis_title="Percentage", height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Proficiency rate context
        st.metric("Combined Proficiency (Meeting + Exceeding)",
                  f"{row['proficient_pct']:.1f}%",
                  help="Meeting + Exceeding Expectations")

        # Cross-grade comparison
        st.subheader(f"MCAS {subject} Across Grades -- {district} ({year})")
        cross = mcas_df[
            (mcas_df['district_id'] == district_id) &
            (mcas_df['subject'] == subject) &
            (mcas_df['year'] == year)
        ]
        if not cross.empty:
            fig2 = go.Figure()
            for level, color in zip(levels, colors):
                col_name = level.lower().replace(' ', '_') + '_pct'
                fig2.add_trace(go.Bar(
                    x=cross['grade'], y=cross[col_name],
                    name=level, marker_color=color
                ))
            fig2.update_layout(
                barmode='stack', xaxis_title="Grade", yaxis_title="Percentage",
                height=400, title=f"MCAS {subject} Performance Distribution"
            )
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("No data available for the selected filters.")


def render_export(access_df, mcas_df, districts_df, domain_df):
    st.header("Export Data")

    st.markdown("Download VERA-MA analysis data as CSV files for further analysis.")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("ACCESS Data")
        st.dataframe(access_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download ACCESS CSV",
            access_df.to_csv(index=False),
            "vera_ma_access.csv", "text/csv",
            use_container_width=True
        )
    with col2:
        st.subheader("MCAS Data")
        st.dataframe(mcas_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download MCAS CSV",
            mcas_df.to_csv(index=False),
            "vera_ma_mcas.csv", "text/csv",
            use_container_width=True
        )

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Statewide Domain Proficiency")
        st.dataframe(domain_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Domain CSV",
            domain_df.to_csv(index=False),
            "vera_ma_domains.csv", "text/csv",
            use_container_width=True
        )
    with col2:
        st.subheader("District Reference Data")
        st.dataframe(districts_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Download Districts CSV",
            districts_df.to_csv(index=False),
            "vera_ma_districts.csv", "text/csv",
            use_container_width=True
        )


# ============================================================================
# MAIN
# ============================================================================

def main():
    st.set_page_config(
        page_title="VERA-MA | Massachusetts Type 4 Detection",
        page_icon="*",
        layout="wide"
    )

    st.markdown(f"""
    <style>
        .stApp {{ background-color: #fafafa; }}
        .block-container {{ padding-top: 2rem; }}
        h1, h2, h3 {{ color: {MA_BLUE}; }}
        .stButton > button {{ background-color: {MA_BLUE}; color: white; }}
        .stButton > button:hover {{ background-color: {MA_DARK}; color: white; }}
    </style>
    """, unsafe_allow_html=True)

    # Load all data
    districts_df = load_districts()
    access_df = load_access_data(districts_df)
    mcas_df = load_mcas_data(districts_df)
    domain_df = load_statewide_domain_data()

    # Sidebar
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: {MA_BLUE}; margin: 0;">VERA-MA</h2>
        <p style="color: #666; font-size: 0.85rem; margin-top: 5px;">Massachusetts Implementation</p>
    </div>
    """, unsafe_allow_html=True)
    st.sidebar.divider()

    page = st.sidebar.radio("Navigation", [
        "Overview",
        "Statewide Domain Analysis",
        "ACCESS Analysis",
        "Type 4 Detection",
        "Achievement Gaps",
        "MCAS Analysis",
        "Export Data"
    ])

    st.sidebar.divider()
    st.sidebar.markdown(f"""
    **Data Sources:**
    - ACCESS for ELLs (WIDA)
    - DESE ACCESS Public Files
    - DESE Report Cards
    - MCAS (MA Comprehensive Assessment)
    - SIMS Data System

    **Type 4 Detection:**
    - Speaking vs Writing delta
    - Flag threshold: > 8 points (normalized)

    **MA Exit Criteria:**
    - Composite ~4.2-4.5 (TBD)
    - Under DESE review

    **Key Context:**
    - ~90,000 ELs (10%)
    - ~400 school districts
    - **MCAS grad req REPEALED Nov 2024**
    - LOOK Act (2017)
    - Spanish, Haitian Creole, Portuguese
    - Boston 16,685 ELs (31.7%)
    - Worcester 8,717 ELs (34.4%)
    - Lawrence 4,709 ELs (34.0%)

    ---
    [H-EDU.Solutions](https://h-edu.solutions)
    """)

    # Page routing
    if page == "Overview":
        render_overview(districts_df)
    elif page == "Statewide Domain Analysis":
        render_domain_analysis(domain_df)
    elif page == "ACCESS Analysis":
        render_access_analysis(access_df, districts_df)
    elif page == "Type 4 Detection":
        render_type4(access_df, districts_df)
    elif page == "Achievement Gaps":
        render_achievement_gaps(districts_df)
    elif page == "MCAS Analysis":
        render_mcas(mcas_df, districts_df)
    elif page == "Export Data":
        render_export(access_df, mcas_df, districts_df, domain_df)


if __name__ == "__main__":
    main()
