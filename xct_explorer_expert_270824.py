#importing all the required packages
import numpy as np            # <2      #Note that the update V2 released June2024 is incompatible
import pandas as pd            # 1.5.3
import streamlit as st          # 1.36.0  #Note that 1.37.0 is incompatible
import altair as alt            # 5.1.2
from streamlit_gsheets import GSheetsConnection   # 0.0.4

st.set_page_config(layout='wide',page_title='XCT-Explorer-Advanced v270824')
tabCitation, tabInstructions, tabGeometry, tabComposition, tabSummary= st.tabs(['Disclosure','Instructions',':blue[Geometric Parameters]',':violet[Composition Parameters]','Summary'])

with tabCitation:
    st.write('The XCT-Explorer-Advanced is a graphic user interface designed to be an intuitive and interactive tool to help planning CT experiments. New users are advised to use the simplified version of this app https://xct-explorer-v1.streamlit.app/. Note that the advanced features are experimental')
    st.subheader ('Citation')
    st.write ('If you find XCT-explorer useful for the planning of your experiment please cite the publication :blue[https://doi.org/10.1016/j.tmater.2024.100041]. The advanced features were not peer-reviewed') 
    st.write ('Advanced features: possibility to add phases that are not in the database, select the filter composition, manualy adjust the filter thickness, export the list of parameters')
    st.subheader('Important disclaimer')
    st.write ('Always interpret the results critically and discuss your assessment with a CT expert')
    st.subheader('GNU Affero General Public License v3.0')
    st.write('Use, reproduction or alteration of the code is possible under the commitment to cite the original work')
    st.write ('https://github.com/godsapt/XCT-Explorer/blob/main/LICENSE')
############################################ Instructions ################################################### 
with tabInstructions:  
    st.write('**Step 1: Define the :blue[Resolution] controlling parameters**')
    st.write('-	Select the purpose of the study')
    st.write('-	Adjust the Sample Diameter slider')
    st.write(' -	If “Minimum Feature Size” is larger than your expectation consider: 1) Increase detector width; 2) Decrease Binning; 3) Decrease Sample Diameter') 
    st.write('**Tip:** Different combinations of binning and detector size may give the same voxel size. In this case choose the combination with higher binning as that reduces the scan time and the data size')
    st.write(' **Step 2: Define the :violet[Composition] of the sample**')
    st.write('-	Select up to 4 of the most relevant Phases in the sample')
    st.write('**Tip:** if the phase is not in the database add the attenuation coefficients to the table and select newPhase 1-3 at the end of the dropdown menu. Add at least 4 values between 40-200kV')
    st.write('-	Input the approximate Volume Fraction for each phase')
    st.write('**Step 3: Tune the X-ray spectra**')
    st.write('-	Select an available filter')
    st.write('- Adjust the filter thickness to remove low energy X-rays (if you are not sure about the filter use https://xct-explorer-v1.streamlit.app/)')
    st.write('-	Adjust the Maximum Energy slider')
    st.write('**Tip:** The best contrast between phases is achieved using a range of energies that maximizes the distance between the attenuation curves (see plot)')
    st.write('**Step 4: Confirm the Time**')
    st.write('-	Input the :green[Number of scans] on the sidebar if more than 1 sample or multiple scans per sample')
    st.write('-	If :red[Experiment Time] is red or warning pops out, consider reducing the scanning time to achieve images with higher quality')
    st.write('-	Confirm that the Experiment Time is realistic for your possibilities')
    st.write('**Tip:** to reduce the scanning time consider the following strategies: 1) reduce Diameter; 2) reduce Filter; 3)	increase Maximum Energy; 4) increase Binning, 5) decrease detector width')
    st.write('- Export the scanning parameters in the **Summary** tab and discusse it with a CT-expert')
    st.write('Note 1: the equations linking the various parameters in the resolution tab is only valid for a specific scanner configuration (in this version is a CoreTOM from Tescan with detector size 2856x2856)')    
    st.write('Note 2: the composition tab uses a database of phases adjusted from Hanna and Ketcham 2017 (10.1016/j.chemer.2017.01.006)')     
    st.write('Note 3: Consider the Experiment Time is just a rough approximation')

@st.cache_data # Currently is using a database uploaded in google sheets. the scanner specific settings could also be loaded 
def loadDatabase():
    #url= "https://docs.google.com/spreadsheets/d/1t8-3UUnGjH2Nv7vF2iHoj5NkEFeWftml9qhTTv3fE4A/edit?usp=sharing"
    # Create a connection object.
    conn = st.connection("gsheets", type=GSheetsConnection)
    phaseData = conn.read()       #if specific url is used (spreadsheet=url)
    return phaseData
database=loadDatabase()
allPhases= database.columns.values.tolist()
newPhases=['newPhase1','newPhase2','newPhase3','newPhase4']
allPhases.extend(newPhases)
allPhases.remove('Energy (kV)')

############################################## state variables ######################################################    
if 'diameter' not in st.session_state:
    st.session_state['diameter']=20
if 'voxelSize' not in st.session_state:
    st.session_state['voxelSize']=10
if 'filterThickness' not in st.session_state:
    st.session_state['filterThickness']=0.05
if 'DataSize' not in st.session_state:
    st.session_state['DataSize']=0.1
if 'maximumEnergy' not in st.session_state:
    st.session_state['maximumEnergy']=100
if 'minimumFeature' not in st.session_state:
    st.session_state['minimumFeature']=30
st.sidebar.title(':blue[Resolution]', help='_"Resolution is not a value but more like a state of mind"_ It depends not only on the voxel size but also on the quality of the final image. Tip: Aim for the highest quality possible, which can save time post-processing the 3D image and will increase the quality of your research')

########################################## Define voxel size vs diameter #################################################
def vs_diameter():
    ########### this is specific of a scanner configuration ### linear equation based on 1920px width (bin1)
    diameters=(12,40,150)                    # diameters 
    VS_1920Bin1=np.array([6,22,83])          # VS for the given diameters. All other correlations are calculated relative to this
    VS_2856Bin1=VS_1920Bin1*2/3
    VS_1920Bin2=VS_1920Bin1*2
    VS_2856Bin2=VS_1920Bin1*2/3*2
    VS_1920Bin3=VS_1920Bin1*3
    VS_2856Bin3=VS_1920Bin1*2/3*3          # this is the same as VS_1920Bin2, so only 5 lines are actually visible in the plot
    ############################# plots ################################
    RegressionData=pd.DataFrame({'Diameter':diameters,'VS_1920Bin1':VS_1920Bin1,'VS_2856Bin1':VS_2856Bin1,'VS_1920Bin2':VS_1920Bin2,'VS_2856Bin2':VS_2856Bin2,'VS_1920Bin3':VS_1920Bin3,'VS_2856Bin3':VS_2856Bin3})
    plotVS_Diam2856B1 = alt.Chart(RegressionData,height=400, width=600).mark_point().encode(x=alt.X('VS_2856Bin1:Q',title='Voxel Size (µm)'),y=alt.Y('Diameter:Q',title='Diameter (mm)')).transform_regression('VS_2856Bin1', 'Diameter').mark_line(color='#17becf',opacity=0.8)
    plotVS_Diam1920B1 = alt.Chart(RegressionData,height=400, width=600).mark_point().encode(x=alt.X('VS_1920Bin1:Q',title='Voxel Size (µm)'),y=alt.Y('Diameter:Q',title='Diameter (mm)')).transform_regression('VS_1920Bin1', 'Diameter').mark_line(color='#1f77b4',opacity=0.8)
    plotVS_Diam2856B2 = alt.Chart(RegressionData,height=400,width=600).mark_point().encode(x=alt.X('VS_2856Bin2:Q',title='Voxel Size (µm)'),y=alt.Y('Diameter:Q',title='Diameter (mm)')).transform_regression('VS_2856Bin2', 'Diameter').mark_line(color='#ff7f0e',opacity=0.8)
    plotVS_Diam1920B2 = alt.Chart(RegressionData,height=400,width=600).mark_point().encode(x=alt.X('VS_1920Bin2:Q',title='Voxel Size (µm)'),y=alt.Y('Diameter:Q',title='Diameter (mm)')).transform_regression('VS_1920Bin2', 'Diameter').mark_line(color='#ffbb78',opacity=0.8)
    plotVS_Diam2856B3 = alt.Chart(RegressionData,height=400,width=600).mark_point().encode(x=alt.X('VS_2856Bin3:Q',title='Voxel Size (µm)'),y=alt.Y('Diameter:Q',title='Diameter (mm)')).transform_regression('VS_2856Bin3', 'Diameter').mark_line(color='#2ca02c',opacity=0.8)
    plotVS_Diam1920B3 = alt.Chart(RegressionData,height=400,width=600).mark_point().encode(x=alt.X('VS_1920Bin3:Q',title='Voxel Size (µm)'),y=alt.Y('Diameter:Q',title='Diameter (mm)')).transform_regression('VS_1920Bin3', 'Diameter').mark_line(color='#98df8a',opacity=0.8)
    plot=plotVS_Diam2856B1 + plotVS_Diam1920B1 +plotVS_Diam2856B2 + plotVS_Diam1920B2 + plotVS_Diam2856B3 + plotVS_Diam1920B3
    if radio3=='1x' and radio4=='1920':
       st.session_state['voxelSize']=int(0.5627*st.session_state['diameter']-0.5293)             #linear correlations ######## in the future the coeficients could be calculated automatically using scipy
       markPoint=pd.DataFrame({'VS':[st.session_state['voxelSize']],'Diam':[st.session_state['diameter']]})   # Red Dot in the plot, coordinates along respective line
       st.session_state['DataSize']=11
    if radio3=='1x' and radio4=='2856':
       st.session_state['voxelSize']=int(0.3626*st.session_state['diameter']+0.0151)
       markPoint=pd.DataFrame({'VS':[st.session_state['voxelSize']],'Diam':[st.session_state['diameter']]})
       st.session_state['DataSize']=32
    if radio3=='2x' and radio4=='1920':
       st.session_state['voxelSize']=int(1.1254*st.session_state['diameter'] -1.0585)       
       markPoint=pd.DataFrame({'VS':[st.session_state['voxelSize']],'Diam':[st.session_state['diameter']]})
       st.session_state['DataSize']=1.4
    if radio3=='2x' and radio4=='2856':
       st.session_state['voxelSize']=int(0.7236*st.session_state['diameter']+0.4404)       
       markPoint=pd.DataFrame({'VS':[st.session_state['voxelSize']],'Diam':[st.session_state['diameter']]})
       st.session_state['DataSize']=4.3
    if radio3=='3x' and radio4=='1920':
       st.session_state['voxelSize']=int(1.6881*st.session_state['diameter']-1.5878)
       markPoint=pd.DataFrame({'VS':[st.session_state['voxelSize']],'Diam':[st.session_state['diameter']]})
       st.session_state['DataSize']=0.4
    if radio3=='3x' and radio4=='2856':
        st.session_state['voxelSize']=int(1.1254*st.session_state['diameter']-1.0585)        
        markPoint=pd.DataFrame({'VS':[st.session_state['voxelSize']],'Diam':[st.session_state['diameter']]})
        st.session_state['DataSize']=1.2
    plotMark = alt.Chart(markPoint,height=400,width=600).mark_point(color='red',size=120,fill='red').encode(x=alt.X('VS:Q',title='Voxel Size (µm)'),y=alt.Y('Diam:Q',title='Diameter (mm)'))
    plotAndMark=plot+plotMark
    st.altair_chart(plotAndMark,use_container_width=False)  

############## Plot Attenuation curves in the Composition Tab ###############################     
def attenuation_energy():
    if menuPhase1 == 'newPhase1':
        plot1= alt.Chart(newDatabase2,width='container',height=400).mark_line(color='lightblue').encode(
                        x=alt.X('Energy (kV):Q').scale(domain=(10,180)),y=alt.Y('newPhase1:Q',title='Attenuation Coefficient (cm-1)').scale(type="log")).interactive()
    else:
        plot1= alt.Chart(database,width='container',height=400).mark_line(color='lightblue').encode(
                        x=alt.X('Energy (kV):Q').scale(domain=(10,180)),y=alt.Y(menuPhase1,title='Attenuation Coefficient (cm-1)').scale(type="log")).interactive()
    if menuPhase2 == 'newPhase2':
        plot2= alt.Chart(newDatabase2,width='container',height=400).mark_line(color='green').encode(
                        x=alt.X('Energy (kV):Q').scale(domain=(10,180)),y=alt.Y('newPhase2:Q',title='Attenuation Coefficient (cm-1)').scale(type="log")).interactive()        
    else:
        plot2= alt.Chart(database,width='container',height=400).mark_line(color='green').encode(
                        x=alt.X('Energy (kV):Q').scale(domain=(10,180)),y=alt.Y(menuPhase2,title='Attenuation Coefficient (cm-1)').scale(type="log")).interactive()
    if menuPhase3 == 'newPhase3':
        plot3= alt.Chart(newDatabase2,width='container',height=400).mark_line(color='green').encode(
                        x=alt.X('Energy (kV):Q').scale(domain=(10,180)),y=alt.Y('newPhase3:Q',title='Attenuation Coefficient (cm-1)').scale(type="log")).interactive()        
    else:
        plot3= alt.Chart(database,width='container',height=400).mark_line(color='green').encode(
                        x=alt.X('Energy (kV):Q').scale(domain=(10,180)),y=alt.Y(menuPhase3,title='Attenuation Coefficient (cm-1)').scale(type="log")).interactive()    
    plot4= alt.Chart(database,width='container',height=400).mark_line(color='red').encode(
                        x=alt.X('Energy (kV):Q').scale(domain=(10,180)),y=alt.Y(menuPhase4,title='Attenuation Coefficient (cm-1)').scale(type="log")).interactive()  
    plot=plot1 + plot2 + plot3 + plot4      
    st.altair_chart(plot,use_container_width=True)
def transmission():
    ########### Lambert-Beer law applied to the seleted phases, volume fractions and sample diameter
    if menuPhase1 == 'newPhase1':
        attPhase1=newDatabase2[menuPhase1]
        attPhase1=attPhase1.astype(float)
        energy= newDatabase2['Energy (kV)']
        energy=energy.astype(float)
    else:
        attPhase1= database[menuPhase1]
        energy= database['Energy (kV)']
    transm1=np.exp(-attPhase1*inFracPhase1*slideDiameter/10)
    if menuPhase2 == 'newPhase1':
        attPhase2=newDatabase2[menuPhase2]
        attPhase2=attPhase2.astype(float)
        energy= newDatabase2['Energy (kV)']
        energy=energy.astype(float)
    else:
        attPhase2= database[menuPhase2]
        energy= database['Energy (kV)']
    transm2=np.exp(-attPhase2*inFracPhase2*slideDiameter/10)
    if menuPhase3 == 'newPhase3':
        attPhase3=newDatabase2[menuPhase3]
        attPhase3=attPhase3.astype(float)
        energy= newDatabase2['Energy (kV)']
        energy=energy.astype(float)
    else:
        attPhase3= database[menuPhase3]
        energy= database['Energy (kV)']
    transm3=np.exp(-attPhase3*inFracPhase3*slideDiameter/10)
    attPhase4= database[menuPhase4]
    transm4=np.exp(-attPhase4*inFracPhase4*slideDiameter/10)
    totalTransm=transm1*transm2*transm3*transm4*100

    ########################### Filter #############################################
    attFilter= database[menuFilter]
    transmFilter=np.exp(-attFilter*st.session_state['filterThickness']/10)*100
    totalTransmFilter=totalTransm*transmFilter/100

    ###################### Plot total transmission ########################################
    TotalTransm4Plot={'Energy (kV)':energy,'Sample':totalTransm,'Filter':transmFilter, 'Filter+Sample':totalTransmFilter}
    dfTotalTransm4Plot=pd.DataFrame(TotalTransm4Plot)
    plotSample= alt.Chart(dfTotalTransm4Plot,width='container',height=400
                    ).mark_line(color='green').encode(x=alt.X('Energy (kV):Q').scale(domain=(20,180)),
                                                            y=alt.Y('Sample',title='Total Transmission (%)').scale(domain=(0,100))).interactive()
    plotSample_Filter=alt.Chart(dfTotalTransm4Plot,width='container',height=400
                    ).mark_line(color='orange').encode(x=alt.X('Energy (kV):Q').scale(domain=(20,180)),
                                                            y=alt.Y('Filter+Sample',title='Total Transmission (%)').scale(domain=(0,100))).interactive()
    plotFilter=alt.Chart(dfTotalTransm4Plot,width='container',height=400
                ).mark_line(color='lightblue').encode(x=alt.X('Energy (kV):Q').scale(domain=(20,180)),
                                                        y=alt.Y('Filter',title='Total Transmission (%)').scale(domain=(0,100))).interactive()
    plot=plotSample+plotSample_Filter+plotFilter
    st.altair_chart(plot,use_container_width=True)
    return dfTotalTransm4Plot

##################### Calculates the minimum feature of interest for the sidebar ############################
def updateMinFeature():
    if radio1=='Qualitative':
        st.session_state['minimumFeature']=st.session_state['voxelSize']*3
    if radio1=='Quantify':
        st.session_state['minimumFeature']=st.session_state['voxelSize']*5
    if radio1=='Classify':
       st.session_state['minimumFeature']=st.session_state['voxelSize']*7

############################ Controls the display in the tab geometry ################################
with tabGeometry:
    colDiam, colPurpose, colBin,colCam = st.columns(4, gap='large')
    with colDiam:
        st.subheader('Sample Diameter (mm)')
        slideDiameter= st.slider(' ', value=20, max_value=150, step=1,help='Larger diameters worsen the resolution. If the sample is irregular input the largest cross-section')
        st.session_state['diameter']=slideDiameter
    with colPurpose:
        st.subheader('Purpose of Study')
        radio1=st.radio(label='   ',options=['Qualitative','Quantify','Classify'], help='What kind of information do you need to answer your scientific question?')
    with colBin:
        st.subheader('Binning')
        radio3=st.radio(label=' ',options=['1x','2x','3x'], help='2x is recommended. Higher binning decreases the scanning time, image artefacts and data size, but worsens voxel size',index=1)
    with colCam:
        st.subheader('Detector width (px)')
        radio4=st.radio(label=' ',options=['2856','1920'],index=1,help='"1920" recommended if very dense phases are present and if the purpose is "Quantify" or "Classify". Smaller detectors decrease cone beam artifacts. Note that other values are possible, the two options are just a guide')
    st.divider()
    st.text('   ') #just some space
    vs_diameter()
    updateMinFeature()
    st.write(':grey[Each line represents a detector setting. The red dot highlights the selected setting]')

################################# Displays sidebar ###########################################
st.sidebar.metric(':blue[Voxel Size (um)]', st.session_state['voxelSize'], 
                  help='Calculated from the selected "Sample Diameter", "Binning" and "Detector width" in the :blue["Geometric Parameters"] tab')
st.sidebar.metric(':blue[Sample diameter (mm)]',st.session_state['diameter'],
                  help='Change with the slider in the :blue["Geometric Parameters"] tab. See the relation Diameter vs Voxel Size in the plot')
st.sidebar.metric(':blue[Minimum Feature Size (um)]', st.session_state['minimumFeature'],
                  help='The size of the smallest feature that you aim to study. It depends on the voxel size and the purpose of the study')
st.sidebar.metric(':blue[Data Size (Gb)]',st.session_state['DataSize'],
                  help='Expected size of the reconstructed 3D image. Relative to binning 1x, binning 2x generates 8x and binning 3x generates 27x smaller images')

############################ Controls the display in the tab Composition ################################
with tabComposition:
    col1,col2,col3,col4=st.columns(4,gap='large')
    with col1:
        st.subheader('Main phases from database', help='The phases of interest are the ones that must be distinguished to answer the scientific question. Tip: if the sample has a complex matrix group the phases into classes of similar attenuation')
        menuPhase1=st.selectbox(label=':blue[Phase1]',options=allPhases,index=0)
        menuPhase2=st.selectbox(label=':green[Phase2]',options=allPhases,index=0) 
        menuPhase3=st.selectbox(label=':orange[Phase3]',options=allPhases,index=0)
        menuPhase4=st.selectbox(label=':red[Phase4]',options=allPhases,index=0)  
######################################################## ADD NEW Phases ########################################################################################
    with col2:
        st.subheader('Add new phases',help='If the phase of interest is not in the database add the attenuation coefficients manually')
        with st.expander('Attenuation coefficients'):
            newDatabase=pd.DataFrame(columns=['Energy (kV)','newPhase1','newPhase2','newPhase3'],index=range(12))
            newDatabase['Energy (kV)']=database['Energy (kV)']
            newDatabase2=st.data_editor(newDatabase, num_rows='dynamic')
    with col3:
        st.subheader('Volume fractions', 
                  help='If you are an x-ray crossing the sample, how much yould you need to cross of each phase (values 0-1 and the sum of all phases should be 1-porosity)')
        inFracPhase1= st.number_input('Phase1 Volume Fraction (0-1)', value=0.0, min_value=0.0, max_value=1.0, step=0.02)
        inFracPhase2= st.number_input('Phase2 Volume Fraction (0-1)', value=0.0, min_value=0.0, max_value=1.0, step=0.02)
        inFracPhase3= st.number_input('Phase3 Volume Fraction (0-1)', value=0.0, min_value=0.0, max_value=1.0, step=0.02)
        inFracPhase4= st.number_input('Phase4 Volume Fraction (0-1)', value=0.0, min_value=0.0, max_value=1.0, step=0.02)
        porosity= int((1-inFracPhase1-inFracPhase2-inFracPhase3-inFracPhase4)*100)    
        st.write('Porosity (%):',porosity) #help='1 minus the sum of the volume fractions. Air is assumed to have attenuation coefficient =0'
    with col4:
        st.subheader('X-ray energy', 
                  help='The x-ray energy spectra ranges from the energy for which the transmission is above approx. 5% (blue curve) and the input "maximum energy"')
        menuFilter=st.selectbox(label='Filter composition',options=('Cu','Fe','Al','Quartz','Polystyrene'),index=1, 
                                help='Filters are tipically metal sheets mounted at the source or sample containers outside the field of view but in the x-ray path. Filters reduce the low energy x-rays that cause image artefacts')
        filterThickness=st.slider('Filter Thickness (mm)', value=0.05,min_value=0.0, max_value=2.5, step=0.1, 
                                  help='The type of filter is decided based on the transmission through the sample. Advise: 1) Check the Energy for which the green curve is 10%. 2) For that energy, aim at getting the blue curve below 50% (ideally less)')
        st.session_state['filterThickness']=filterThickness
        st.text('   ') #just some space
        testEmax=st.slider('Maximum Energy (kV)', value=160, min_value=0, max_value=180, step=5,help='Tip: aim at a 160 kV, only use lower if necessary for good contrast')
        st.session_state['maximumEnergy']=testEmax

############################ Display plots ################################
    st.divider()
    col5,col4=st.columns(2,gap='large')
    with col4:
        st.subheader('Total transmission',
                  help='Percent of x-rays that penetrate through the :blue[Filter (light blue)], the :green[Sample (green)] and the :orange[Sample + Filter (orange)] at various energies')
        dfTotalTransm4Plot2 = transmission()
        st.write(':green[Sample]  -  :blue[Filter]  -  :orange[Sample+Filter]')
        with st.expander('Transmission Table'):
            st.table(dfTotalTransm4Plot2)    
    with col5:
        st.subheader('Attenuation',
                  help='Energies with large difference between curves give better contrast. Note: if the curves are matching the phases will have similar greyvalues in the final image)')
        attenuation_energy()
        st.write(':grey[Each line corresponds to a phase selected with the same color]')

############################ Controls the sidebar ################################
st.sidebar.title('  ') #just some space
st.sidebar.title(':violet[Contrast]', 
                 help='Contrast is reflected in the grey-scale of the different phases in the final image. It can be estimated by the difference in the attenuation curves within the energies boundaries [minimum transmissible energy, Emax], see Attenuation plot in the tab :violet["Composition"]')
st.sidebar.metric(':violet[Maximum Energy (kV)]',st.session_state['maximumEnergy'],help='Input with the slider in the tab :violet["Composition Parameter"]. Tip: 1) If contrast is not a problem, aim at high kV, 2) At Emax, the transmission should be at least 10percent ')
st.sidebar.metric(':violet[Filter]',st.session_state['filterThickness'],menuFilter, delta_color='off' )
############################ Calculation of time using empirical equations ################################
if st.session_state['voxelSize']<15:      # this is specific of the CoreTom: the power (W) equals the voxel size except bellow 15um.
    power = 15
else:
    power = st.session_state['voxelSize']
if radio3=='1x' and radio4=='1920':
    cameraFactor=1 # this camera was used as reference
    resolutionFactor=1
    scanTime=round((1.38*st.session_state['filterThickness']-0.0198*st.session_state['maximumEnergy']-0.0328*power+6.048)*cameraFactor,1)
if radio3=='2x' and radio4=='1920':
    cameraFactor=1
    resolutionFactor=2
    scanTime=round((0.68*st.session_state['filterThickness']-0.0109*st.session_state['maximumEnergy']-0.0152*power+2.607)*cameraFactor,1)
if radio3=='3x' and radio4=='1920':
    cameraFactor=1
    resolutionFactor=3 
    scanTime=round((0.328*st.session_state['filterThickness']-0.0055*st.session_state['maximumEnergy']-0.0068*power+1.19)*cameraFactor,1)
if radio3=='1x' and radio4=='2856':
    cameraFactor=1.4875
    resolutionFactor=1
    scanTime=round((1.38*st.session_state['filterThickness']-0.0198*st.session_state['maximumEnergy']-0.0328*power+6.048)*cameraFactor,1)
if radio3=='2x' and radio4=='2856':
    cameraFactor=1.4875
    resolutionFactor=2
    scanTime=round((0.68*st.session_state['filterThickness']-0.0109*st.session_state['maximumEnergy']-0.0152*power+2.607)*cameraFactor,1)
if radio3=='3x' and radio4=='2856':
    cameraFactor=1.4875
    resolutionFactor=3
    scanTime=round((0.328*st.session_state['filterThickness']-0.0055*st.session_state['maximumEnergy']-0.0068*power+1.19)*cameraFactor,1)
if scanTime<0.1:
    scanTime=0.1
#Unused time equation with binning as input 
#scanTime=(0.61*st.session_state['filterThickness']-0.0109*st.session_state['maximumEnergy']-1.3*resolutionFactor-0.0148*st.session_state['voxelSize']+5.65)*cameraFactor   #Bin1+Bin2+Bin3

st.sidebar.title(' ') #just some space
st.sidebar.title(':green[Time]',help='Tip: longer scans usually mean higher quality, which means less image processing time. Restric the time only if it is a time-lapse experiment or the access to the scanner is limited')
inNumbScans= st.sidebar.number_input(':green[Number of scans]', value=1, min_value=1, max_value=100, step=1, 
                                     help='this should acount for 1) how many samples, 2) how many scans per sample, e.g if the sample height> 0.8 x diameter. :red[IMPORTANT: Only aim at as many samples as you can realistically analyse]. Rule of thumb: processing 1 scan takes at least 1 days for qualitative studies and 1 week for quantitative studies')
experimentTime=round((scanTime+0.2)*inNumbScans,1) # adds 0.2 hrs to account for warmup?

if radio3=='1x' and radio4=='2856' and scanTime>6.2:
    st.sidebar.metric(':red[Experiment Time (hrs)]',experimentTime) 
elif radio3=='2x' and radio4=='2856' and scanTime>3.2:
    st.sidebar.metric(':red[Experiment Time (hrs)]',experimentTime)
elif radio3=='3x' and radio4=='2856' and scanTime>2.2:
    st.sidebar.metric(':red[Experiment Time (hrs)]',experimentTime)
elif radio3=='1x' and radio4=='1920' and scanTime>4.2:
    st.sidebar.metric(':red[Experiment Time (hrs)]',experimentTime) 
elif radio3=='2x' and radio4=='1920' and scanTime>2.2:
    st.sidebar.metric(':red[Experiment Time (hrs)]',experimentTime)
elif radio3=='3x' and radio4=='1920' and scanTime>1.5:
    st.sidebar.metric(':red[Experiment Time (hrs)]',experimentTime)
else: 
    st.sidebar.metric(':green[Experiment Time (hrs)]',experimentTime,help='It includes 12 min for every scan (to warmup and setting up the scan)') 

with tabSummary:
    buttExport=st.button(label='Export parameters')
    if buttExport:
        scanParameters={'Parameter':['Voxel Size (um)','Purpose', 'Binning', 'Detector size','Energy', 'Filter Material','Filter Thickness (um)','Data Size (Gb)','Expected time (hrs)'],
                        'Value':[st.session_state['voxelSize'],radio1,radio3,radio4,st.session_state['maximumEnergy'],menuFilter,st.session_state['filterThickness'],st.session_state['DataSize'],scanTime],
                        'Sample':['Sample Diameter (mm)','Phase1','Fraction Phase1','Phase2','Fraction Phase2','Phase3','Fraction Phase3','Phase4','Fraction Phase4'],
                        'Composition':[st.session_state['diameter'],menuPhase1,inFracPhase1,menuPhase2,inFracPhase2,menuPhase3,inFracPhase3,menuPhase4,inFracPhase4]}
        scanParameters=pd.DataFrame(scanParameters)
        st.dataframe(scanParameters, width=800,hide_index=True)
        #pd.DataFrame.to_csv()
