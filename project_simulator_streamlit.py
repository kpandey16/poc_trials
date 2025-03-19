import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Configure page
st.set_page_config(page_title="Project Risk Simulator", layout="wide")

# Initial configuration
DEFAULT_STAGES = {
    1: {'name': 'Planning', 'baseline': 6, 'risks': [
        {'type': 'funding', 'probability': 0.2, 'impact': (1, 3), 
         'severity': 'high', 'mitigation': 'emergency budget allocation'}
    ]},
    2: {'name': 'Surveying', 'baseline': 6, 'risks': [
        {'type': 'logistics', 'probability': 0.3, 'impact': (1, 2),
         'severity': 'medium', 'mitigation': 'alternative transport'}
    ]},
    3: {'name': 'Fund Allocation', 'baseline': 6, 'risks': []},
    4: {'name': 'Procurement', 'baseline': 6, 'risks': [
        {'type': 'supply_chain', 'probability': 0.4, 'impact': (2, 4),
         'severity': 'critical', 'mitigation': 'multiple suppliers'},
        {'type': 'logistics', 'probability': 0.25, 'impact': (1, 3),
         'severity': 'medium', 'mitigation': 'local warehouses'}
    ]},
    5: {'name': 'Installation', 'baseline': 6, 'risks': [
        {'type': 'labor', 'probability': 0.35, 'impact': (1, 4),
         'severity': 'high', 'mitigation': 'training programs'}
    ]},
    6: {'name': 'Quality Check', 'baseline': 6, 'risks': []}
}

def create_stage_controls():
    """Create interactive controls for stage parameters"""
    modified_stages = {}
    total_baseline = 0
    
    for stage_num in DEFAULT_STAGES:
        stage = DEFAULT_STAGES[stage_num]
        with st.expander(f"Stage {stage_num}: {stage['name']}", expanded=False):
            # Baseline duration control
            new_baseline = st.number_input(
                "Baseline duration (months)",
                min_value=1,
                max_value=24,
                value=stage['baseline'],
                key=f"stage_{stage_num}_baseline"
            )
            total_baseline += new_baseline

            # Risk controls
            modified_risks = []
            for risk_idx, risk in enumerate(stage['risks']):
                st.markdown(f"**{risk['type'].title()} Risk**")
                
                # Probability slider
                new_prob = st.slider(
                    "Probability",
                    min_value=0.0,
                    max_value=1.0,
                    value=risk['probability'],
                    step=0.05,
                    key=f"stage_{stage_num}_risk_{risk_idx}_prob"
                )
                
                # Impact controls
                col1, col2 = st.columns(2)
                with col1:
                    impact_min = st.number_input(
                        "Min impact (months)",
                        min_value=0,
                        max_value=24,
                        value=risk['impact'][0],
                        key=f"stage_{stage_num}_risk_{risk_idx}_min"
                    )
                with col2:
                    impact_max = st.number_input(
                        "Max impact (months)",
                        min_value=impact_min,
                        max_value=24,
                        value=risk['impact'][1],
                        key=f"stage_{stage_num}_risk_{risk_idx}_max"
                    )
                
                modified_risks.append({
                    **risk,
                    'probability': new_prob,
                    'impact': (impact_min, impact_max)
                })
            
            modified_stages[stage_num] = {
                'name': stage['name'],
                'baseline': new_baseline,
                'risks': modified_risks
            }
    
    return modified_stages, total_baseline

def simulate_project(stages):
    total_delay = 0
    cumulative_duration = 0
    risk_log = []
    
    for stage_num in stages:
        stage = stages[stage_num]
        stage_duration = stage['baseline']
        
        for risk in stage['risks']:
            if np.random.random() < risk['probability']:
                delay = np.random.randint(risk['impact'][0], risk['impact'][1]+1)
                stage_duration += delay
                total_delay += delay
                
                risk_log.append({
                    'stage': stage_num,
                    'type': risk['type'],
                    'severity': risk['severity'],
                    'delay': delay,
                    'mitigation': risk['mitigation']
                })
                
        cumulative_duration += stage_duration
        
    return total_delay, cumulative_duration, risk_log

def run_simulation(stages, num_simulations):
    results = []
    risk_register = []
    
    for _ in range(num_simulations):
        delay, duration, risks = simulate_project(stages)
        results.append({'delay': delay, 'duration': duration})
        risk_register.extend(risks)
        
    return pd.DataFrame(results), pd.DataFrame(risk_register)

def main():
    st.title("🏗️ Project Risk Simulator")
    
    # Sidebar controls
    with st.sidebar:
        st.header("Simulation Controls")
        total_baseline = st.empty()

        num_simulations = st.number_input(
            "Number of simulations",
            min_value=1000,
            max_value=100000,
            value=10000
        )


    st.header("Project Stage Configuration")
    modified_stages, calculated_baseline = create_stage_controls()

    with st.container():
        total_baseline.metric("Total Baseline Duration", f"{calculated_baseline} months")

    # Stage configuration
    
    
    # Run simulation
    if st.button("🚀 Run Simulation", type="primary"):
        with st.spinner(f"Running {num_simulations} simulations..."):
            results_df, risks_df = run_simulation(modified_stages, num_simulations)
            
            # Display results
            st.success("Simulation completed!")
            st.subheader("Key Metrics")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Probability of delay", 
                        f"{(results_df['duration'] > 36).mean():.2%}")
            col2.metric("Average delay", 
                        f"{results_df['delay'].mean():.1f} months")
            col3.metric("Max delay observed", 
                        f"{results_df['delay'].max()} months")
            
            # Visualizations
            st.subheader("Risk Analysis")
            tab1, tab2, tab3 = st.tabs(["Risk Distribution", "Delay Impact", "Mitigation Strategies"])
            
            with tab1:
                fig, ax = plt.subplots(figsize=(8, 6))
                risks_df['type'].value_counts().plot.pie(autopct='%1.1f%%', ax=ax)
                st.pyplot(fig)
            
            with tab2:
                fig, ax = plt.subplots(figsize=(10, 6))
                risks_df.groupby('type')['delay'].mean().sort_values().plot.barh(ax=ax)
                ax.set_xlabel("Average Delay (months)")
                st.pyplot(fig)

            with tab3:
                mitigation_table = risks_df.groupby(['type', 'mitigation']).size().unstack(fill_value=0)
                st.dataframe(mitigation_table.style.highlight_max(axis=1))
            
            # Raw data
            with st.expander("📊 View Detailed Results"):
                st.subheader("Simulation Data")
                st.dataframe(results_df.describe().T, use_container_width=True)
                st.download_button(
                    "📥 Download Results",
                    data=results_df.to_csv().encode('utf-8'),
                    file_name="simulation_results.csv"
                )

if __name__ == "__main__":
    main()
