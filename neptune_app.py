import numpy as np
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="NEPTUNE v6.1 Simulator", page_icon="🌊", layout="wide")

# ---------- COLOURS ----------
INK, TEAL, CORAL, AMBER, SAND, MIST = "#0E2A47", "#1B8A8F", "#E4572E", "#E9A23B", "#F3F7F8", "#D5E3E7"

# ---------- STYLE ----------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700&family=Source+Sans+3:wght@400;600&display=swap');
html, body, [class*="css"] {{ font-family: 'Source Sans 3', sans-serif; color: {INK}; }}
.stApp {{ background: {SAND}; }}
h1, h2, h3 {{ font-family: 'Bricolage Grotesque', sans-serif !important; color: {INK}; }}
section[data-testid="stSidebar"] {{ background: {INK}; }}
section[data-testid="stSidebar"] * {{ color: #EAF3F5 !important; }}
.hero {{ background: linear-gradient(120deg, {INK} 0%, #14507A 60%, {TEAL} 100%);
        padding: 28px 32px; border-radius: 20px; margin-bottom: 18px; }}
.hero h1 {{ color: #fff !important; margin: 0; font-size: 2rem; }}
.hero p {{ color: #CFE6EA; margin: 6px 0 0 0; }}
.card {{ background: #fff; border-radius: 16px; padding: 16px 18px; border: 1px solid {MIST};
        border-top: 5px solid var(--c); height: 100%; }}
.card .k {{ font-size: .85rem; color: #5B7186; }}
.card .v {{ font-family: 'Bricolage Grotesque', sans-serif; font-size: 1.6rem; font-weight: 700; line-height: 1.2; }}
.card .s {{ font-size: .9rem; font-weight: 600; color: var(--c); }}
.note {{ background: #fff; border-left: 5px solid {TEAL}; padding: 12px 16px; border-radius: 10px; margin-top: 8px; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>NEPTUNE v6.1 Simulator</h1>
  <p>See how the polymer dose changes the PAR condensate, and whether the drug picks the right target.</p>
</div>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
st.sidebar.markdown("## Controls")
np_ratio = st.sidebar.slider("Polymer dose (c / c_crit)", 0.0, 2.0, 0.65, 0.05,
    help="Below 1.0 = Plan A (blocks the space). At 1.0 or more = Plan B (condensate turns solid).")
xi_thresh = st.sidebar.slider("PEG charge filter (ξ threshold)", 3.0, 8.0, 5.5, 0.1,
    help="Polyanions with charge density ξ below this value are ignored by the polymer.")
rescue_cap = st.sidebar.slider("Cell rescue capacity (%)", 0, 100, 15, 5,
    help="How well the cell clears the polymer (Hsp70/Hsp100). High in healthy cells, low in stressed tumour cells.")
probe = st.sidebar.radio("Molecule moving through the mesh",
    ["Small tracer (1.5 nm)", "PARG / XRCC1 complex (6.5 nm)"], index=1)
r_s = 1.5 if probe.startswith("Small") else 6.5

# ---------- MODEL ----------
NU, R_FIBER, K_L, K_EXP = 1.35, 1.2, 0.012, 1.3

def fiber_length(c):          # fibre length per volume (nm^-2)
    return K_L * np.power(c, K_EXP)

def ogston(c, r):             # fraction of space a probe of radius r can enter
    return np.exp(-np.pi * fiber_length(c) * (r + R_FIBER) ** 2)

c_eff = max(0.0, np_ratio - (rescue_cap / 100) * 0.65)
L = fiber_length(c_eff)
# Mesh size now comes from the same fibre length, so the numbers always agree
R_mesh = min(40.0, 1 / np.sqrt(L)) if L > 0 else 40.0
steric_ratio = 2 * r_s / R_mesh
f_probe = float(ogston(c_eff, r_s))
d_macro = (1 - c_eff) ** NU if c_eff < 1 else 0.0

if xi_thresh <= 4.2:
    tier2 = 2.5
elif xi_thresh <= 7.0:
    tier2 = 18.0 * (1 - abs(5.5 - xi_thresh) / 3.0)
else:
    tier2 = 1.5
SI = 7.0 * max(1.0, tier2)

if c_eff == 0:
    regime, rc = "Cleared", TEAL
elif c_eff < 0.35:
    regime, rc = "Sub-threshold", AMBER
elif c_eff < 1.0:
    regime, rc = "Plan A: blocking", TEAL
else:
    regime, rc = "Plan B: solid", CORAL

def card(col, title, value, sub, colour):
    col.markdown(f'<div class="card" style="--c:{colour}"><div class="k">{title}</div>'
                 f'<div class="v">{value}</div><div class="s">{sub}</div></div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
card(c1, "Condensate state", regime, f"effective dose {c_eff:.2f}", rc)
card(c2, "Probe size / mesh size", f"{steric_ratio:.2f}",
     "Blocked" if steric_ratio >= 1 else "Can get through", CORAL if steric_ratio >= 1 else TEAL)
card(c3, "Free space for probe", f"{f_probe*100:.1f}%", f"bulk movement {d_macro*100:.0f}%", INK)
card(c4, "Selectivity (SI)", f"{SI:.0f}x", "Meets 100x goal" if SI >= 100 else "Below 100x goal",
     TEAL if SI >= 100 else CORAL)

# ---------- CHARTS ----------
def style(fig, title, h=440):
    fig.update_layout(title=dict(text=title, font=dict(family="Bricolage Grotesque", size=18, color=INK)),
        height=h, paper_bgcolor="#fff", plot_bgcolor="#fff", font=dict(family="Source Sans 3", color=INK),
        legend=dict(orientation="h", y=-0.25), margin=dict(l=20, r=20, t=60, b=20))
    fig.update_xaxes(gridcolor="#EEF3F5", zeroline=False)
    fig.update_yaxes(gridcolor="#EEF3F5", zeroline=False)
    return fig

st.write("")
tab1, tab2 = st.tabs(["Mesh and movement", "Charge filter"])

with tab1:
    c = np.linspace(0, 1.8, 200)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=c, y=np.where(c < 1, (1 - c) ** NU, 0), name="Bulk movement",
                             line=dict(color=TEAL, width=3)))
    fig.add_trace(go.Scatter(x=c, y=ogston(c, 1.5), name="Free space, small tracer",
                             line=dict(color=INK, width=2, dash="dot")))
    fig.add_trace(go.Scatter(x=c, y=ogston(c, 6.5), name="Free space, PARG / XRCC1",
                             line=dict(color=CORAL, width=3)))
    fig.add_vline(x=c_eff, line_dash="dash", line_color=AMBER, line_width=2,
                  annotation_text=f"You are here ({c_eff:.2f})")
    fig.add_vline(x=1.0, line_color=CORAL, line_width=1, annotation_text="c_crit")
    fig.update_xaxes(title="Polymer dose (c / c_crit)")
    fig.update_yaxes(title="Fraction (0 to 1)", range=[0, 1.05])
    st.plotly_chart(style(fig, "Large enzymes get blocked long before the whole condensate turns solid"),
                    use_container_width=True)
    st.markdown('<div class="note">Small molecules still move at low doses, but the 6.5 nm repair complex '
                'loses space quickly. That is why Plan A works before Plan B starts.</div>', unsafe_allow_html=True)

with tab2:
    names = ["Duplex DNA", "Unbranched PAR", "Branched PAR"]
    xi = [4.2, 7.0, 14.0]
    cols = [CORAL if x < xi_thresh else TEAL for x in xi]
    fig = go.Figure(go.Bar(x=names, y=xi, marker_color=cols,
        text=[f"ξ = {x}<br>condensed = {1 - 1/x:.2f}" for x in xi], textposition="auto"))
    fig.add_hline(y=xi_thresh, line_dash="dash", line_color=AMBER, line_width=3,
                  annotation_text=f"Filter ξ = {xi_thresh}")
    fig.update_yaxes(title="Charge density (ξ)")
    st.plotly_chart(style(fig, "Teal = polymer binds it. Red = polymer ignores it.", 420),
                    use_container_width=True)
    st.markdown('<div class="note">Best selectivity is around ξ = 5.5: high enough to ignore DNA, '
                'low enough to still grab PAR.</div>', unsafe_allow_html=True)
