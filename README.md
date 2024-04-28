# Read Me Energy Range and Consumption Estimator 

#Using the app:

This project can be reached via the public URL: https://energy-estimator.streamlit.app/
However, building the project and corresponding website may take some time if it has not been accessed for a couple of days. Just click the button in the middle of the screen to rebuild it.

1. To use the site, please enter a departure destination (e.g. HPI)
2. Choose one of the results in the appearing list and
3. Repeat for the destination (e.g. using Babelsberg as destination).
4. The selected departure and destination should be highlighted in red.You should see that both GPS coordinates (start lat/long and end lat/long) now show the corresponding coordinates (NOT 0.0). 
5. Scroll down in the sidebar and click on the "Create Dashboard" button


#Developing the app: 

This app has been developed using https://streamlit.io/, an open-source source app framework to develop user interfaces in Python. Combining its frontend capabilities with plotly (https://plotly.com/) allows the creation of off-the-shelf interactive data visualizations. 

To checkout the code and make alterations:

Prequesits: 
- Anaconda Navigator is installed
- This github repo has been cloned

1. Create a conda environment using the .yml file
     - navigate to the folder of the energy_estimator.yml file in the console
     - conda env create -f energy_estimator.yml
2. Activate the conda environment
     - conda activate env_energy_estimator
3. Run the streamlit app from the console
   - streamlit run src/app.py
4. Open your web browser to see local instance of the app running on http://localhost:8501/


#Other remarks: 
- The map.html file is generated automatically when creating the dashboard. It is then used to display the map view in the dashboard.
- Please keep in mind that the developed heuristic did not prove to be a valid reflection of reality. Testing the dashboard, please use distances <5km to nevertheless get a rough approximation of range and consumption.
- The bar plot does not add up to 100% as the distance, as the main driver of the consumption, is not part of the visualization.
- The requirements.txt file is needed for the streamlit web visualization. 

