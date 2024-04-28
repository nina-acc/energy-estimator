# Read Me Energy Range and Consumption Estimator 

#Using the app:

This project can be reached via the public URL: https://energy-estimator.streamlit.app/
However, building the project and corresponding website may take some time if has not been accessed for a couple of days. Just click the button in the middle of the screen to rebuild it.

1. To use the site, please enter a departure destination (e.g. HPI)
2. Choose one of the results in the appearing list and
3. Repeat for the destination. You should see that both GPS coordinates (start lat/long and end lat/long) should show the corresponding coordinates (NOT 0.0).
4. click on "Create Dashboard 


#Developing the app: 

This app has been developed using https://streamlit.io/, an open-source source app framework to develop user interfaces in python. Combining it's frontend capabilities with plotly  (https://plotly.com/) allows the creation off-the-shelf interactive data visualizations. 

To checkout the code and make alterations:

Prequesits: 
- Anaconda Navigator is installed
- This github repo has been cloned

1. Create a conda environment using the requirements.txt file
     - navigate to the folder of the requirements.txt file in the console
     - conda create --name env_energy_estimator --file requirements.txt
2. Activate the conda environment
     - conda activate env_energy_estimator
3. Run the streamlit app from the console
   - streamlit run src/app.py


