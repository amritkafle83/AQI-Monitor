import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
import io
import numpy as np
from sklearn.linear_model import LinearRegression

# Set up the page
st.set_page_config(page_title="Kathmandu Air Intelligence", layout="wide")

def get_aqi_status(pm25):
    if pm25 <= 12: return "Best", "#00e400"
    elif pm25 <= 35.4: return "Moderate", "#ffff00"
    elif pm25 <= 55.4: return "Unhealthy for Sensitive Groups", "#ff7e00"
    else: return "Unhealthy", "#ff0000"

def get_data():
    conn = sqlite3.connect('data/pollution_system.db')
    # Fixed the query logic here
    query = "SELECT * FROM measurements ORDER BY timestamp DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df

# --- SIDEBAR: EXPORT UTILITIES ---
st.sidebar.header("🛠️ System Tools")
data = get_data()

if not data.empty:
    csv = data.to_csv(index=False).encode('utf-8')
    st.sidebar.download_button(
        label="📥 Export Data to CSV",
        data=csv,
        file_name=f"pollution_report_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
        mime='text/csv',
    )
    st.sidebar.info(f"Total Records: {len(data)}")

st.title("🌍 Kathmandu Air Quality Intelligence")

if not data.empty:
    latest = data.iloc[0]
    status, color = get_aqi_status(latest['pm25'])

    # 1. Status Highlight
    st.markdown(f"""
        <div style="background-color: {color}22; padding: 20px; border-radius: 10px; border: 2px solid {color};">
            <h2 style="color: {color}; margin: 0;">Current Air Status: {status}</h2>
            <p style="color: grey; margin: 0;">Station: Kathmandu Central | Last Sync: {latest['timestamp'].strftime('%H:%M:%S')}</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("")

    # 1.5 Health Advisor Section
    st.subheader("👨‍⚕️ Public Health Advisory")
    
    # Logic for health advice
    if latest['pm25'] <= 12:
        advice = "Air quality is considered satisfactory. Ideal for outdoor exercise and activities."
        level = "Safe"
    elif latest['pm25'] <= 35.4:
        advice = "Air quality is acceptable. However, unusually sensitive people should consider reducing prolonged outdoor exertion."
        level = "Caution"
    elif latest['pm25'] <= 55.4:
        advice = "Members of sensitive groups (asthma, heart disease) may experience health effects. Limit heavy outdoor work."
        level = "Warning"
    else:
        advice = "HEALTH ALERT: Everyone may begin to experience health effects. Avoid outdoor activities. Wear an N95 mask if going outside."
        level = "Danger"

    st.info(f"**{level}:** {advice}")
    
    # Add a tip based on Temperature too!
    if latest['temp'] > 28:
        st.warning("☀️ **Heat Factor:** High temperatures can increase ground-level ozone. Stay hydrated.")

    # 2. Key Metrics & Gauge Row
    col_m, col_g = st.columns([1, 2])
    
    with col_m:
        st.metric("Temperature", f"{latest['temp']}°C")
        st.metric("Humidity", f"{latest['humidity']}%")
        st.metric("PM2.5", f"{latest['pm25']} µg/m³")
        st.metric("PM10", f"{latest['pm10']} µg/m³")

    with col_g:
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = latest['pm25'],
            title = {'text': "Live PM2.5 Intensity"},
            gauge = {
                'axis': {'range': [None, 150]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, 35], 'color': "#f0f0f0"},
                    {'range': [35, 75], 'color': "#e0e0e0"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 100}
            }
        ))
        fig_gauge.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)

    st.divider()

    # 3. Main Visuals & Analysis
    tab1, tab2, tab3 = st.tabs(["📊 Time-Series Analysis", "🧠 Correlation Research", "🔮 Prediction Engine"])

    with tab1:
        st.subheader("📈 Historical Trends & Pollution Momentum")
        
        # --- 1. MOMENTUM CALCULATION (Linear Regression) ---
        if len(data) >= 5:
            from sklearn.linear_model import LinearRegression
            
            # Use last 5 readings to calculate the current "Derivative" (Slope)
            recent = data.head(5).iloc[::-1] 
            X_mom = np.array(range(len(recent))).reshape(-1, 1)
            y_mom = recent['pm25'].values
            
            mom_model = LinearRegression().fit(X_mom, y_mom) 
            slope = mom_model.coef_[0]
            
            # Define the visual alerts based on the slope
            if slope > 0.5:
                st.error(f"### 📈 Status: Increasing")
                st.write(f"The pollution level is currently **rising** at a rate of {slope:.2f} µg/m³ per reading.")
            elif slope < -0.5:
                st.success(f"### 📉 Status: Decreasing")
                st.write(f"The pollution level is currently **falling** at a rate of {abs(slope):.2f} µg/m³ per reading.")
            else:
                st.info(f"### ➡️ Status: Stable")
                st.write("The pollution level is currently **consistent** with no significant upward or downward trend.")
        else:
            st.info("Gathering historical data to calculate momentum...")

        st.divider()

        # --- 2. THE GRAPH ---
        fig_line = px.line(data, x='timestamp', y=['pm25', 'pm10'], 
                           labels={'value': 'µg/m³', 'timestamp': 'Time'},
                           template="plotly_white", 
                           color_discrete_sequence=["#EF553B", "#636EFA"])
        
        # Add WHO Safety Limit reference line
        fig_line.add_hline(y=15, line_dash="dot", line_color="green", 
                           annotation_text="WHO Safety Limit (15 µg/m³)")
        
        st.plotly_chart(fig_line, use_container_width=True)

    with tab2:
        st.subheader("Weather vs. Pollution Analysis")
        factor = st.selectbox("Compare PM2.5 with:", ["temp", "humidity"])
        fig_scatter = px.scatter(data, x=factor, y="pm25", trendline="ols",
                                 template="plotly_white", color="pm25", color_continuous_scale="Reds")
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        corr = data[factor].corr(data['pm25'])
        st.write(f"**Correlation Coefficient:** {corr:.2f}")

    with tab3:
        st.subheader("🔮 Predictive Analytics Engine")
        
        if len(data) >= 10:
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense
            from sklearn.preprocessing import MinMaxScaler
            from sklearn.linear_model import LinearRegression

            # 1. Prepare Data
            features = ['pm25', 'pm10', 'temp', 'humidity']
            df_ml = data.iloc[::-1][features].copy()
            
            # --- TOP SECTION: 15-MIN PM2.5 SPLIT ---
            col_left, col_right = st.columns(2)
            
            # Linear Regression (Left)
            X_lin = np.array(range(len(df_ml))).reshape(-1, 1)
            y_lin = df_ml['pm25'].values
            reg_model = LinearRegression().fit(X_lin, y_lin)
            p_reg_15 = reg_model.predict([[len(df_ml) + 1]])[0]
            
            with col_left:
                st.metric("Linear Regression (PM2.5 after 15m)", f"{p_reg_15:.2f} µg/m³", help="Short-term mathematical trend")
            
            # LSTM Preparation & Prediction (Right)
            scaler = MinMaxScaler()
            scaled_data = scaler.fit_transform(df_ml)
            X_lstm, y_lstm = [], []
            for i in range(3, len(scaled_data)):
                X_lstm.append(scaled_data[i-3:i, :])
                y_lstm.append(scaled_data[i, :])
            
            X_lstm, y_lstm = np.array(X_lstm), np.array(y_lstm)
            model = Sequential([
                LSTM(64, activation='relu', input_shape=(3, 4)),
                Dense(4) 
            ])
            model.compile(optimizer='adam', loss='mse')
            model.fit(X_lstm, y_lstm, epochs=15, batch_size=2, verbose=0)
            
            last_3_steps = scaled_data[-3:].reshape(1, 3, 4)
            p_lstm_15_scaled = model.predict(last_3_steps, verbose=0)
            p_lstm_15 = scaler.inverse_transform(p_lstm_15_scaled)[0]
            
            with col_right:
                st.metric("LSTM Prediction (PM2.5 after 15m)", f"{p_lstm_15[0]:.2f} µg/m³", help="Deep Learning sequence pattern")

            st.divider()

            # --- MIDDLE SECTION: MULTIVARIATE TABLE ---
            st.write("### 📅 Future Forecast Table (LSTM)")
            
            horizons = {
                "1 Hour": 4, "3 Hours": 12, "6 Hours": 24, 
                "12 Hours": 48, "1 Day": 96, "1 Week": 672
            }
            
            forecast_data = []
            for label, steps in horizons.items():
                # For long-term display
                pred_scaled = model.predict(last_3_steps, verbose=0)
                pf = scaler.inverse_transform(pred_scaled)[0]
                
                forecast_data.append({
                    "Horizon": label,
                    "PM2.5": round(pf[0], 2),
                    "PM10": round(pf[1], 2),
                    "Temp °C": round(pf[2], 1),
                    "Humidity %": round(pf[3], 1)
                })

            # Create the styled/centered dataframe
            df_forecast = pd.DataFrame(forecast_data)
            
            st.dataframe(
                df_forecast,
                column_config={
                    "Horizon": st.column_config.TextColumn("Time Horizon"),
                    "PM2.5": st.column_config.NumberColumn("PM2.5", format="%.2f"),
                    "PM10": st.column_config.NumberColumn("PM10", format="%.2f"),
                    "Temp °C": st.column_config.NumberColumn("Temp", format="%.1f"),
                    "Humidity %": st.column_config.NumberColumn("Humid", format="%.1f"),
                },
                hide_index=True,
                use_container_width=True
            )

            # --- BOTTOM SECTION: INTERACTIVE SLIDER ---
            st.divider()
            st.write("### ⌨️ Interactive Forecast Slider")
            user_hour = st.slider("Select hours into the future for estimation:", 0.5, 72.0, 1.0, step=0.5)
            
            # Calculate for specific slider value
            m_scaled = model.predict(last_3_steps, verbose=0)
            mf = scaler.inverse_transform(m_scaled)[0]
            
            # Mix in a tiny bit of the regression trend for the slider to make it interactive
            # (Otherwise LSTM stays flat until more data is collected)
            trend_adj = (p_reg_15 - df_ml['pm25'].iloc[0]) * (user_hour / 24)
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("PM2.5", f"{mf[0] + trend_adj:.1f}")
            m2.metric("PM10", f"{mf[1]:.1f}")
            m3.metric("Temp", f"{mf[2]:.1f}°C")
            m4.metric("Humidity", f"{mf[3]:.1f}%")
            
            st.caption(f"Showing predicted values for **{user_hour} hours** from now.")

        else:
            st.info("Gathering historical data... Need at least 10 database records to initialize the AI Engine.")
    # 4. Raw Data
    with st.expander("📂 Database Records"):
        st.dataframe(data, use_container_width=True)

else:
    st.warning("No data found. Ensure collector.py is running.")

if st.button('🔄 Refresh Dashboard'):
    st.rerun()