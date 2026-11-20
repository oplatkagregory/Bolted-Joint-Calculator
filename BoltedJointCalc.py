import numpy as np
import math as ma
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Joint Calculator", page_icon="⚙️")
st.title("🔩 Bolted Joint Calculator")

# 1. Initialize session state variables
if "step" not in st.session_state:
    st.session_state.step = 1

if "user_data" not in st.session_state:
    st.session_state.user_data = {}

# Helper functions to manage moving between steps
def next_step():
    st.session_state.step += 1

# def prev_step():
#     st.session_state.step -= 1

def reset_wizard():
    st.session_state.step = 1
    st.session_state.user_data = {}

# 2. Display progress bar or visual indicator
st.progress((st.session_state.step) / 4)
st.write(f"**Step {st.session_state.step} of 4**")
st.divider()

notes = "Assumptions: \n" \
    "1. Frustum angle = 30° \n" \
    "2. Thread angle = 60° \n" \
    "\n" \
    "References: \n" \
    "1. R. G. Budynas and J. K. Nisbett, 'Shigley's Mechanical Engineering Design, 11th edition,' McGraw-Hill, Jan 2019."

def materialLib(material):
    if material == "6061-T6 Al":
        return np.array([68.9e9, 276e6])
    elif material == "304 SS":
        return np.array([196e9, 205e6])
    elif material == "932 Bronze":
        return np.array([196e9, 205e6])
    elif material == "Other":
        print("Add to material library")
        return np.array([0, 0])

class Joint:
    def __init__(self, numMembers, materials, thicknesses, boltDiameter):
        self.numMembers = numMembers
        self.materials = materials
        self.thicknesses = thicknesses
        self.width = np.sum(thicknesses)
        self.boltDiameter = boltDiameter

    def coords(self):
        self.yCoords = np.zeros((self.numMembers,2),dtype=float)
        for m in range(self.numMembers):
            if m > 0:
                self.yCoords[m,0] = self.yCoords[m-1,1]
                self.yCoords[m,1] = self.yCoords[m,0] + self.thicknesses[m]
            else:
                self.yCoords[m,1] = self.thicknesses[m]

    def splitMembers(self):

        # Split members into two members if they straddle the frustum mirror plane
        
        for m in range(self.numMembers):
            if self.yCoords[m,0] < self.width/2.0 and self.yCoords[m,1] > self.width/2.0:
                self.numMembers = self.numMembers + 1
                self.materials = np.insert(self.materials, m, self.materials[m,:], axis=0)
                self.thicknesses = np.insert(self.thicknesses, m, self.width/2.0 - self.yCoords[m,0], axis=0)
                self.thicknesses[m+1] = self.thicknesses[m+1] - self.thicknesses[m]
                self.coords()

    def calcDiameters(self):

        self.diameters = np.zeros((self.numMembers,2),dtype=float)
        dw = 1.5 * self.boltDiameter

        for m in range(self.numMembers):
            if self.yCoords[m,1] <= self.width/2.0:
                self.diameters[m,0] = dw + 2*ma.tan(ma.pi/6)*self.yCoords[m,0]
                self.diameters[m,1] = dw + 2*ma.tan(ma.pi/6)*self.yCoords[m,1]
            else:
                self.diameters[m,0] = dw + -2*ma.tan(ma.pi/6)*self.yCoords[m,0] + 2*ma.tan(ma.pi/6)*self.width
                self.diameters[m,1] = dw + -2*ma.tan(ma.pi/6)*self.yCoords[m,1] + 2*ma.tan(ma.pi/6)*self.width

    def calcStiffnesses(self):

        self.stiffnesses = np.zeros((self.numMembers),dtype=float)

        for m in range(self.numMembers):
            dI = 0
            dO = 0
            if self.diameters[m,0] > self.diameters[m,1]:
                dI = self.boltDiameter
                dO = self.diameters[m,1]
            else:
                dI = self.boltDiameter
                dO = self.diameters[m,0]
                
            self.stiffnesses[m] = ((0.5774 * ma.pi * self.materials[m,0] * dI)/
                                (ma.log(((1.155 * self.thicknesses[m] + dO - dI)*(dO + dI))/
                                    ((1.155 * self.thicknesses[m] + dO + dI)*(dO - dI)))))

    def get_stiffnesses(self):
        self.coords()
        self.splitMembers()
        self.calcDiameters()
        self.calcStiffnesses()

        return self.stiffnesses


# ==========================================
# Bolt Parameters and Number of Members
# ==========================================
if st.session_state.step == 1:
    st.subheader("Bolt Parameters and Number of Members")
    
    boltSize = st.number_input("What is the bolt diameter (mm)?", min_value=0.0, max_value=200.0, value = 6.0, step=0.5)/1000
    pitch = st.number_input("What is the thread pitch (mm)?", min_value=0.0, max_value=40.0, value = 1.0, step=0.1)/1000
    tsArea = (ma.pi*0.25*(boltSize - 0.9382*pitch)**2)

    boltMaterial = st.selectbox(
            "Select the bolt material:",
            options=["304 SS", "6061-T6 Al", "932 Bronze", "Other"]
        )
    boltMat = materialLib(boltMaterial)

    partiallyThreaded = st.checkbox("Check box if bolts are partially threaded?")

    numBolts = int(st.number_input("How many bolts are there?", min_value=1, max_value=100, value=4))

    percentPreload = st.number_input("What is the percent preload as a decimal?", min_value=0.0, max_value=1.0, value = 0.65, step=0.01)
    preload = numBolts*percentPreload*tsArea*0.9*boltMat[1]

    numMembers = int(st.number_input("How many members are there (include washers)?", min_value=1, max_value=100, value=2))

    flexibleElements = int(st.number_input(
        "How many face sealing elements are there (ex: O-Ring, Canted Coil Spring; All face sealing elements assumed to be in parallel)?",
                                            min_value=0, max_value=100, value=0))

    extLoad = st.number_input("What is the external load on the joint (N; Tensile loads are positive)?", value = 500.0, step=0.1)

    
    if st.button("Next ➡️"):
        st.session_state.user_data["boltSize"] = boltSize
        st.session_state.user_data["pitch"] = pitch
        st.session_state.user_data["tsArea"] = tsArea
        st.session_state.user_data["boltMaterial"] = boltMaterial
        st.session_state.user_data["boltMat"] = boltMat
        st.session_state.user_data["partiallyThreaded"] = partiallyThreaded
        st.session_state.user_data["numBolts"] = numBolts
        st.session_state.user_data["percentPreload"] = percentPreload
        st.session_state.user_data["preload"] = preload
        st.session_state.user_data["numMembers"] = numMembers
        st.session_state.user_data["flexibleElements"] = flexibleElements
        st.session_state.user_data["extLoad"] = extLoad
        next_step()
        st.rerun()

    st.write(notes)
# ==========================================
# Member Parameters
# ==========================================
elif st.session_state.step == 2:
    st.subheader("Member Parameters")
    st.write("For screws, do NOT include the member with the threaded hole(s).")

    numMembers = st.session_state.user_data["numMembers"]
    memberThicknesses = np.zeros((numMembers),dtype=float)
    memberMats = np.zeros((numMembers, 2),dtype=float)
    memberMaterials = [""] * numMembers


    for m in range(numMembers):
        memberThicknesses[m] = st.number_input("How thick is member " + str(m + 1) + " (mm)?", value=25.0)/1000
        memberMaterials[m] = st.selectbox("What is the member " + str(m + 1) + " material?",
                            options=["6061-T6 Al", "304 SS", "932 Bronze", "Other"])
        memberMats[m,:] = materialLib(memberMaterials[m])

    threadFrictCoeff = st.number_input("What is the thread friction coefficient?", min_value=0.0, max_value=2.0, value=0.25)
    collarFrictCoeff = st.number_input("What is the collar friction coefficient?", min_value=0.0, max_value=2.0, value=0.25)

    flexibleElements = st.session_state.user_data["flexibleElements"]
    springLoads = np.zeros((flexibleElements),dtype=float)
    if flexibleElements > 0:
        for i in range(flexibleElements):
            springLoads[i] = st.number_input("What is the compressive load required to compress flexible element " + str(i + 1) + " (N)?", value=1000.0)

    if st.button("Next ➡️"):
        st.session_state.user_data["memberThicknesses"] = memberThicknesses
        st.session_state.user_data["memberMats"] = memberMats
        st.session_state.user_data["memberMaterials"] = memberMaterials
        st.session_state.user_data["threadFrictCoeff"] = threadFrictCoeff
        st.session_state.user_data["collarFrictCoeff"] = collarFrictCoeff
        st.session_state.user_data["springLoads"] = springLoads
        partiallyThreaded = st.session_state.user_data["partiallyThreaded"]
        if partiallyThreaded:
            next_step()
            st.rerun()
        else:
            st.session_state.step += 2
            st.rerun()

    st.write(notes)

# ==========================================
# Joint Diagram and Results
# ==========================================
elif st.session_state.step == 4:
    st.subheader("Joint Diagram")

    numMembers = st.session_state.user_data["numMembers"]
    memberMats = st.session_state.user_data["memberMats"]
    memberThicknesses = st.session_state.user_data["memberThicknesses"]
    boltSize = st.session_state.user_data["boltSize"]
    joint1 = Joint(numMembers, memberMats, memberThicknesses, boltSize)
    stiffnesses = joint1.get_stiffnesses()
    invStiffnesses = 1/stiffnesses
    kM = 1/np.sum(invStiffnesses)

    majDiamArea = ma.pi*0.25*boltSize**2
    tsArea = st.session_state.user_data["tsArea"]
    boltMat = st.session_state.user_data["boltMat"]
    lg = np.sum(memberThicknesses)

    lt = 0
    ld = 0
    partiallyThreaded = st.session_state.user_data["partiallyThreaded"]
    if partiallyThreaded:
        unthreadedLg = st.session_state.user_data["unthreadedLg"]
        lt = lg - unthreadedLg
        ld = unthreadedLg
    else:
        lt = lg
    
    boltStiffness = (majDiamArea*tsArea*boltMat[0])/(majDiamArea*lt + tsArea*ld)
    numBolts = st.session_state.user_data["numBolts"]

    kB = numBolts*boltStiffness

    c = kB/(kB + kM)

    extLoad = st.session_state.user_data["extLoad"] + np.sum(st.session_state.user_data["springLoads"])
    preload = st.session_state.user_data["preload"]
    pB = c*extLoad
    pM = (1 - c)*extLoad

    xB = np.linspace(0, max(((preload + pB)/kB), (preload/kB)), 5)
    yB = kB*xB

    xM = np.linspace(-max((preload/kM), ((preload - pM)/kM)), 0, 5)
    yM = -kM*xM

    fig, ax = plt.subplots()
    
    # Plot the data
    plt.plot(1000*xB, yB, label=f"y = {kB}x + {0}")
    plt.plot(1000*xM, yM, label=f"y = {kM}x + {0}")
    preloadPtsX, preloadPtsY = [1000*(preload/kB),1000*(-preload/kM)], [preload, preload]
    # plt.plot((preload/kB), preload, 'o', color='red')
    # plt.plot((-preload/kM), preload, 'o', color='red')
    extLoadPtsX, extLoadPtsY = [1000*((preload+pB)/kB),1000*(-(preload - pM)/kM)], [(preload + pB), (preload - pM)]
    # plt.plot(((preload+pB)/kB), (preload + pB), 'o', color='green')
    # plt.plot((-(preload - pM)/kM), (preload - pM), 'o', color='green')
    plt.scatter(preloadPtsX, preloadPtsY, color='red', label='Preload')
    plt.scatter(extLoadPtsX, extLoadPtsY, color='green', label='Preload and External Load')
    plt.xlabel("Displacement (mm)")
    plt.ylabel("Force (N)")
    plt.title("Joint Diagram")
    plt.axhline(0, color="black", linewidth=0.5)
    plt.axvline(0, color="black", linewidth=0.5)
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.legend(loc='lower right')
    # plt.show()

    st.pyplot(fig)

    pitch = st.session_state.user_data["pitch"]
    boltMaterial = st.session_state.user_data["boltMaterial"]
    memberMaterials = st.session_state.user_data["memberMaterials"]
    percentPreload = st.session_state.user_data["percentPreload"]

    threadFrictCoeff = st.session_state.user_data["threadFrictCoeff"]
    collarFrictCoeff = st.session_state.user_data["collarFrictCoeff"]
    meanDiam = boltSize - 0.6495*pitch
    installationTorque = 0.5*(preload/numBolts)*meanDiam*(pitch + ma.pi*threadFrictCoeff*meanDiam*\
                        (1/ma.cos(ma.pi/6)))*(1/(ma.pi*meanDiam - threadFrictCoeff*pitch*\
                        (1/ma.cos(ma.pi/6)))) + collarFrictCoeff*(preload/numBolts)*0.5*1.25*boltSize

    if extLoad > 0:
        jointSepFOS = preload/pM
        boltYieldFOS = (numBolts*tsArea*0.9*boltMat[1])/(preload + pB)
        overloadingFOS = (tsArea*0.9*boltMat[1] - (preload/numBolts))/(pB/numBolts)
    else:
        jointSepFOS = 0
        boltYieldFOS = (numBolts*tsArea*0.9*boltMat[1])/(preload)
        overloadingFOS = 0

    inputs = {
        "Parameter": ["Bolt Diameter (mm)", "Thread Pitch (mm)", "Threaded Length of Bolt in Joint (mm)",
                       "Unthreaded Length of Bolt in Joint (mm)", "Number of Bolts", "Percent Preload", "External Load (N)"],
        "Value": [boltSize*1000, pitch*1000, lt*1000, ld*1000, numBolts, percentPreload, extLoad]
    }

    memberProps = {
        "Member Material": memberMaterials,
        "Member Thickness (mm)": 1000*memberThicknesses
    }

    outputs = {
            "Parameter": ["Stiffness of Bolt(s) (N/m)", "Stiffness of Member(s) (N/m)", "Fraction of External Load on Bolt(s)",
                           "Preload per Bolt (N)", "Installation Torque (Nm)", "Joint Separation FOS", "Bolt Yielding FOS",
                           "Bolt Overloading FOS"],
            "Value": [kB, kM, c, preload/numBolts, installationTorque, jointSepFOS, boltYieldFOS, overloadingFOS]
        }

    st.subheader("Summary of Inputs")

    st.table(pd.DataFrame(inputs))

    st.write("Bolt Material: " + boltMaterial)

    st.table(pd.DataFrame(memberProps))

    st.subheader("Summary of Outputs")

    st.table(pd.DataFrame(outputs))

    # data = st.session_state.user_data
    # st.json(data)
    
    if st.button("Start Over"):
            reset_wizard()
            st.rerun()

    st.write(notes)

# ==========================================
# Additional step for partially threaded bolts
# ==========================================

elif st.session_state.step == 3:
    st.subheader("Partially Threaded Bolt Parameters")

    memberThicknesses = st.session_state.user_data["memberThicknesses"]
    lg = np.sum(memberThicknesses)
    partiallyThreaded = st.session_state.user_data["partiallyThreaded"]
    unthreadedLg = st.number_input("What is the UNTHREADED length of the bolt (mm)?", min_value=0.0, max_value=1000*lg, step=0.01)/1000
    if st.button("Next ➡️"):
        st.session_state.user_data["unthreadedLg"] = unthreadedLg
        st.session_state.step = 4
        st.rerun()

    st.write(notes)