import pandas as pd
import numpy as np
import panel as pn
pn.extension('tabulator')



import hvplot.pandas  # DO NOT DELETE THIS LINE
import hvplot.streamz  # noqa
#from streamz.dataframe import Random
from streamz import Stream
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import os
import param

import holoviews as hv
import threading
from collections import deque
import asyncio
from bleak import BleakClient, BleakError

""" global vars"""
global pstate1, pstate2, pstate3, pstate4, pstate5, pstate6, pstate7
pstate1=0
pstate2=0
pstate3=0
pstate4=0
pstate5=0
pstate6=0
pstate7=0


# Create a custom class to handle the image display
class ImageDisplayer(param.Parameterized):
    visible = param.Boolean(default=False)

    def __init__(self, **params):
        super().__init__(**params)
        self.image_pane = pn.pane.Image('assets/Messaging.png', visible=self.visible,
                                        width=400, height=300, align=('center', 'center'))
        self.hide_callback = None

    @param.depends('visible', watch=True)
    def _update_visibility(self):
        self.image_pane.visible = self.visible

    def show_image(self):
        if self.hide_callback is not None:
            self.hide_callback.stop()
        self.visible = True
        # Schedule hiding the image after 3 seconds
        self.hide_callback = pn.state.add_periodic_callback(self.hide_image, period=3000, count=1)

    def hide_image(self):
        self.visible = False
        if self.hide_callback is not None:
            self.hide_callback.stop()
            self.hide_callback = None


# Create an instance of ImageDisplayer
image_displayer = ImageDisplayer()




async def connectBLE(address, uuid):
    """ Bleak BLE  """
    # Define the Bluetooth device's MAC address and the UUID of the characteristic you want to use

    # Bleak:  To discover Bluetooth devices that can be connected to:
    # Define the asyncio coroutine to handle the Bluetooth communication
    # async def main(address):

    """  bleak.discover(): discover nearby BLE devices that are advertising their presence. When you call bleak.discover(),
    it returns a list of BleakService objects, each of which represents a BLE device that was discovered.
    You can then use the BleakClient class to connect to one of these devices and interact with its services."""

    """BleakScanner: provides a more flexible way to discover BLE devices.  It allows you to set up a callback 
    function that will be called whenever a new device is discovered, and you can also specify filters for the 
    devices you want to discover based on criteria such as device name, service UUID, or manufacturer data."""

    """ Providing an address or UUID instead of a BLEDevice causes the connect() method to implicitly call BleakScanner.discover().
    This is known to cause problems when trying to connect to multiple devices at the same time. """

    #devices = await BleakScanner.discover()

    #for d in devices:
    #    if 'SEEED-WJ' in d.name:
    async with BleakClient(address) as client:
        print(
            f"Connected: {client.is_connected}")  # It is also possible to connect and disconnect without a context manager, however this can leave the device still connected when the program exits:

        # paired = await client.pair(protection_level=2)
        # print(f"Paired: {paired}")

        """ char_specifier: Union[BleakGATTCharacteristic, int, str, UUID] """
        model_number = await client.read_gatt_char(
            uuid)  # gatt + characteristics (most I/O with a device done this way)
        print("Model Number: {0}".format("".join(map(chr, model_number))))

        # subscribe to notifications
        await client.start_notify(uuid, handle_notification)

        # # Wait for notifications to come in
        while True:
            await asyncio.sleep(0.1)

    # # Start the asyncio loop and run the coroutine
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(run())


async def BLE_asyncThread():
    max_retries = 4  # Set the maximum number of connection retries
    retry_delay = 3 # Delay between retries in seconds

    for attempt in range(max_retries):
        try:
            async with BleakClient(central_address) as client:
                if not client.is_connected:
                    print(f"Connection attempt {attempt + 1} failed, retrying...")
                    continue

                print(f"Connected on attempt {attempt + 1}")

                # Start notifications
                await client.start_notify(gesture_uuid, handle_notification)

                global gBLE_received
                while client.is_connected:
                    await asyncio.sleep(1.0)
                    if gBLE_received:
                        await client.write_gatt_char(someother_uuid, bytearray(0))
                        gBLE_received = False

                # Stop notifications and disconnect
                await client.stop_notify(gesture_uuid)
                break  # Exit loop if successful

        except BleakError as e:
            print(f"BLE Error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print("Maximum retry attempts reached. Connection failed.")

        except Exception as e:
            print(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print("Maximum retry attempts reached. Connection failed.")

            # async with BleakClient(central_address) as client:
            #     while True:
            #         #model_number = await client.read_gatt_char(gesture_uuid)
            #
            #         #print("BLE: {0}".format("".join(map(chr, model_number))))
            #
            #         #print(f'Temperature: {temperature}')
            #         # subscribe to notifications
            #
            #         await client.start_notify(gesture_uuid, handle_notification)
            #
            #         # # Wait for notifications to come in
            #         global gBLE_received
            #         while True:
            #             await asyncio.sleep(1.0)
            #             if (gBLE_received):
            #                 await client.write_gatt_char(someother_uuid, bytearray(current))
            #                 gBLE_received= False
            #         # Stop notifications and disconnect
            #         await client.stop_notify(uuid)


async def handle_notification(sender, data):
    """
        Handle incoming notifications from the BLE device
    """
    global pstate1, pstate2, pstate3, pstate4, pstate5, pstate6, pstate7
    global current
    global decoded_state
    global gBLE_received, gestureBLE_received_for_textfield
    global mode_class, gStepcount, gStepcount_prev,  gStepcount_updated, gStepcount_offset
    global global_idle_count
    global is_free_fall, gFree_fall_display_count
    global ble_1st_connection

    print(f"Received notification: {data}")
    csv = data.decode().split(',')
    print(csv)
    mode_class = csv[0];  #  a: freefall, b: activity, c: step count report

    if mode_class == 'a':
        print("This is a free fall event")
        is_free_fall = True
        gFree_fall_display_count = 6
        decoded_state = int(csv[1])
        pstate1 = csv[2]  # probabilities based on softmax
        pstate2 = csv[3]
        pstate3 = csv[4]
        pstate4 = csv[5]
        # pstate5 = csv[6]
        # pstate6 = csv[7]
        pstate7 = 0  # idle assignment
        gBLE_received = True
        #gestureBLE_received_for_textfield = True
        global_idle_count = 0  # reset the idle count since there was a gesture

        image_displayer.show_image()


    elif mode_class =='b':
        print("Tihs is an activity")

        decoded_state = int(csv[1])
        pstate1 = csv[2] # probabilities based on softmax
        pstate2 = csv[3]
        pstate3 = csv[4]
        pstate4 = csv[5]
        # pstate5 = csv[6]
        # pstate6 = csv[7]
        pstate7 = 0  # idle assignment
        gBLE_received = True
        gestureBLE_received_for_textfield = True
        global_idle_count = 0  # reset the idle count since there was a gesture

        """ 2D grid visualizer update """
        update_grid(decoded_state)


        """Update the indicators dynamically with the received values"""
        prone_indicator.value = float(pstate1) * 100
        stand2sit_indicator.value = float(pstate2) * 100
        supine_indicator.value = float(pstate3) * 100
        walking_indicator.value = float(pstate4) * 100

    elif mode_class == 'c':
        print("This is a step count reporting")

        #decoded_state = int(csv[1])
        gStepcount = int(csv[1])



        if ble_1st_connection:
            gStepcount_offset = gStepcount
            ble_1st_connection = False
        gBLE_received = True
        gStepcount_updated = True

        gStepcount_rate = gStepcount - gStepcount_prev
        gStepcount_rate_capped = 20 if gStepcount_rate>20 else gStepcount_rate
        # Update the plot immediately after receiving gStepcount
        #update_plot()
        receive_gStepcount(gStepcount, gStepcount_rate_capped)
        #update_gStepcount(gStepcount, gStepcount_rate_capped)
        gStepcount_prev = gStepcount


global gStepcount, gStepcount_prev
#global gStepcount_rate
#gStepcount_rate=0 #initialize
gStepcount_prev=0 #initialize
global time_index
time_index= 0 # start from 0

""" This part is for setting up the 2D grid plot for activity class visualization (next 100 lines)"""
# Define the grid size (e.g., 10x10)
grid_size = 12
grid = np.full((grid_size, grid_size), 4)  # Initialize with 0



grid0 = np.full((grid_size, grid_size), -1)  # Initialize with -1 (no data)


# Define the colormap (using a ListedColormap)
# cmap = plt.cm.get_cmap('viridis', 5)  # Choose a colormap with 4 discrete colors
class_colors = {
    0: '#1f77b4',  # Blue for walking (class 0)
    1: '#9467bd',  # green now #'#9467bd',  # Purple for supine (class 1)
    2: '#ff7f0e',  # Orange for prone (class 2)
    3: '#2ca02c',   # Green for standing (class 3)
    4: '#02080d',   #black for fall (class 4)
}

# Convert class_colors to a list for use in the colormap
color_list = [class_colors[key] for key in sorted(class_colors.keys())]

# Create a custom colormap from the class colors
cmap = plt.cm.colors.ListedColormap(color_list)

# Create a legend using Matplotlib patches
legend_handles = [
    Patch(color=class_colors[0], label='Prone'),
    Patch(color=class_colors[1], label='Stand-to-sit'),
    Patch(color=class_colors[2], label='Supine'),
    Patch(color=class_colors[3], label='Walk'),
    Patch(color=class_colors[4], label='Stand'),
]

# Initialize Matplotlib figure and axes
fig, ax = plt.subplots()
ax.set_xticks([])
ax.set_yticks([])

# Update function to add new data
def update_grid(activity_class):
    global grid, fig
    grid = np.roll(grid, -1, axis=1)  # Shift all columns left
    grid[:, -1] = np.roll(grid[:, -1], -1)  # Shift the last column up
    grid[-1, -1] = list(class_colors.keys()).index(activity_class)  # Add new data to the last square

    # Update the plot
    ax.clear()

    ax.imshow(grid, cmap=cmap, vmin=0, vmax=4)  #Plot with custom colormap
    ax.set_xlabel("Time (seconds)", fontsize=20)
    ax.set_ylabel("Time (Minutes)", fontsize=20)
    ax.set_xticks(np.arange(len(time_x_label)), labels=time_x_label)
    ax.set_yticks(np.arange(len(time_y_label)), labels=time_y_label)
    # ax.set_title("Activity History for last hours", fontsize=25, fontweight='bold')

    # Add the legend outside the grid
    ax.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1, 1),
               fontsize='large')  # Font size increased
    fig.subplots_adjust(left=0.1, right=0.85,top=0.96)

    # Update the pane with the new figure
    grid_plot_pane.object = fig

# Create the Matplotlib pane
grid_plot_pane = pn.pane.Matplotlib(fig, sizing_mode='stretch_both')
grid_plot_pane_title = pn.pane.HTML("<div style='font-size: 30px; font-weight: bold;'>Activity History </div>")





""" New Live Plot of gStepCount"""
# Set up deque to store gStepcount for last 120 seconds
gStepcount_data = deque(maxlen=24)  # Storing 120 seconds, assuming 1 data point every 5 seconds
gStepcount_rate_data = deque(maxlen=24)  # Storing 120 seconds, assuming 1 data point every 5 seconds
activity_data= deque(maxlen=24)
time_data = deque(maxlen=24)  # For timestamps


# Panel IntSlider to reflect the latest time window (optional)

def update_slider_range(event):
    time_slider.start = max(event.new - 40, 0)  # Ensures the start doesn't go below 0
    time_slider.end = event.new + 40

time_slider = pn.widgets.IntSlider(name='Time Window', start=0, end=500, step=5, value=150)




# cache data to improve dashboard performance
if 'data' not in pn.state.cache.keys():

    df = pd.read_csv('activity_past_data.csv')
    pn.state.cache['data'] = df.copy()
else:
    df = pn.state.cache['data']

# Fill NAs with 0s and create GDP per capita column
df = df.fillna(0)
activity_label=['Prone', 'Stand-to-sit', 'Supine','Walk', 'Stand']#, 'Fall']
# Define the activity classes
activity_classes = {
    0: 'Prone',
    1: 'Stand-to-sit',
    2: 'Supine',
    3: 'Walk',
    4: 'Stand'
}

# Create a dictionary mapping from activityclass to activitylabel
label_mapping = {i: activity_label[i] for i in range(len(activity_label))}

# Map the activityclass column to activitylabel
df['activitylabel'] = df['activityclass'].map(label_mapping)

# Calculate stepcount_rate as the difference between the current and previous row
df['stepcount_rate'] = df['stepcount'].diff().fillna(0)

# Make DataFrame Pipeline Interactive
idf = df.interactive()



""" This for the first row static grid plot for activity history example"""
# def draw_static_grid(index):
#     global grid0
#
#     # Assuming df['activity_class'] is a column in your DataFrame
#     activity_classes = df['activityclass'].values
#     xgrid_sizse=10
#     ygrid_sizse=10
#     grid_area = xgrid_sizse*ygrid_sizse
#
#
#     #filtered_start_index = max(index-50, 0)
#     filtered_last_index = min(index+50, len(df)-50)
#
#    #rint(filtered_start_index)
#     print(filtered_last_index)
#     # Reshape the activity classes into a 10x10 grid
#     grid0 = activity_classes[:100].reshape((xgrid_sizse, ygrid_sizse))
#
#     # Update the plot
#     ax.clear()
#     ax.imshow(grid0, cmap=cmap, vmin=0, vmax=4)  # Adjust vmax according to the number of classes
#     ax.set_xticks([])
#     ax.set_yticks([])
#
#     # Add the legend outside the grid
#     ax.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(1.05, 1), fontsize='large')
#
#     # Update the pane with the new figure
#     grid_static_plot_pane.object = fig
#
#
# # # Create the Matplotlib pane
# grid_static_plot_pane = pn.pane.Matplotlib(fig)
#
# draw_static_grid(0) #initialize
#
# # Bind the function to the slider value
# grid_static_plot_pane = pn.bind(lambda index: pn.pane.Matplotlib(draw_static_grid(index)), time_slider)

# Initial plot creation

time_y_label = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"]
time_x_label = ["0", "5", "10", "15", "20", "25",
                "30", "35", "40", "45", "50", "55", "60"]


def create_grid_plot(index):
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    fig1.subplots_adjust(left=0.1, right=0.85,top=0.96)
    if index + 1 >= 144:
        grid_data = df['activityclass'].iloc[index - 143: index + 1].values.reshape((12, 12))
    else:
        grid_data = np.zeros((12, 12))  # or handle it some other way

    # grid_data = df['activityclass'].iloc[:index + 1].values.reshape((10, 10))
    im = ax1.imshow(grid_data, cmap=cmap, vmin=0, vmax=4) #Set1
    ax1.set_xlabel("Time (seconds)", fontsize=20)
    ax1.set_ylabel("Time (minutes)", fontsize=20)
    ax1.set_xticks(np.arange(len(time_x_label)), labels=time_x_label)
    ax1.set_yticks(np.arange(len(time_y_label)), labels=time_y_label)
    #ax1.set_title("Activity History for last 12 minutes", fontsize=30, fontweight='bold')

    # Add the legend outside the grid
    ax1.legend(handles=legend_handles, loc='upper right', bbox_to_anchor=(1.55, 1), fontsize=20)  # Font size increased



    return fig1

# Panel for the plot
index = 144  # Initial index
fig1 = create_grid_plot(index)
grid_static_plot_pane = pn.pane.Matplotlib(fig1, sizing_mode='stretch_both')

# Callback to update the plot when the slider changes
def update_grid_plot(event):
    index = event.new
    fig = create_grid_plot(index)
    grid_static_plot_pane.object = fig


time_slider.param.watch(update_grid_plot, 'value')










#year_slider = 1750 + gStepcount
# Radio buttons for CO2 measures
# yaxis_co2 = pn.widgets.RadioButtonGroup(
#     name='Y axis',
#     options=['co2', 'co2_per_capita', ],
#     button_type='success'
# )
# continents = ['World', 'Asia', 'Oceania', 'Europe', 'Africa', 'North America', 'South America', 'Antarctica']

step_pipeline = (
    idf[
        (idf.time <= time_slider)
        # &
        # (idf.country.isin(continents))
        ]
    # .groupby(['time', 'activitylabel'])['stepcount'].mean()
    # .to_frame()
    .reset_index()
    .sort_values(by='time')
    .reset_index(drop=True)
)

""" original graphs """
step_plot = step_pipeline.hvplot(x='time', y='stepcount', line_width=2, title="Total Steps")
step_rate_plot = step_pipeline.hvplot(x='time', y='stepcount_rate', line_width=2, title="Steps per time", kind='bar')


step_plot_title = pn.pane.HTML("<div style='font-size: 35px; font-weight: bold;'>Cumultive Activity </div>")
step_rate_plot_title = pn.pane.HTML("<div style='font-size: 35px; font-weight: bold;'>Activity Rate </div>")


""" This part is for summary statistics and histogram (next 20 lines) """


# Adding Histogram and Stats
def calculate_activity_trends(df, index):
    # Determine the subset to consider
    if index + 1 >= 144:
        subset = df['activityclass'].iloc[index - 143: index + 1].values.reshape((12, 12))
    else:
        subset = df['activityclass'].iloc[:index + 1].values.reshape((12, 12))

    # Group every 12 data points as one row
    rows = subset.reshape(-1, 12)

    # Calculate the percentage for each class in each row
    class_percentages = {i: np.sum(rows == i, axis=1) / 12 * 100 for i in range(len(activity_label))}  # Assuming 4 classes: 0, 1, 2, 3

    # Create a DataFrame for the bar plot
    trend_df = pd.DataFrame(class_percentages)
    trend_df.index = [f'{i}' for i in range(trend_df.shape[0])]

    # Create the stacked bar plot
    bar_plot = trend_df.hvplot.bar(stacked=True, sizing_mode='stretch_both',
                                   color=[class_colors[i] for i in range(len(activity_label))],
                                xlabel='Time (Min)', ylabel='Activity Percentage (%)',
                                   legend='top_right', width=600)

    # Calculate trend statistics
    initial_percentages = trend_df.iloc[0]
    final_percentages = trend_df.iloc[-1]
    trend_stats = final_percentages - initial_percentages

    # Create a Markdown pane for displaying the trend statistics
    stats_text = "\n".join(
        [f"**{activity} Trend:** {trend:.2f}% change from first row to last row"
         for activity, trend in trend_stats.items()])

    stats_pane = pn.pane.Markdown(stats_text, width=500)

    return pn.Column(bar_plot, stats_pane)


# Initial histogram and stats
activity_trends_pane = calculate_activity_trends(df, index)


# Function to update histogram and stats
def update_activity_trends(event):
    index = event.new
    activity_trends_pane.objects = [calculate_activity_trends(df, index)]


time_slider.param.watch(update_activity_trends, 'value')

"""  -------------------------------   """



# Function to simulate new data being added
# Function to simulate new data being added
# Not used now because it failed to integrate with df.hvplot.bar
# def append_data(new_time, new_stepcount):
#     global df, idf
#     new_data = pd.DataFrame({'Time': [new_time], 'gStepcount': [new_stepcount]})
#     df = pd.concat([df, new_data], ignore_index=True)
#     idf =  df.interactive()



# """ STREAM PLOT TEST  (next 50 lines)"""
# # Create a stream
# stream = Stream()
#
# # Function to emit data to the stream
# def update_gStepcount(gStepcount, gStepcount_rate):
#     print("in update_gStepcount")
#     print(gStepcount)
#     print(gStepcount_rate)
#     data = pd.DataFrame({'time': [pd.Timestamp.now()], 'gStepcount': [gStepcount], 'gStepcount_rate': [gStepcount_rate]})
#     # Emit the DataFrame to the stream
#     stream.emit(data)
#
# # Create a dataframe from the stream
# df_stream = stream.to_dataframe(example={'time': [], 'gStepcount': [], 'gStepcount_rate': []})
#
# live_stepcount_plot = df_stream.hvplot(x='time', y='gStepcount',
#                                           title="Live Step counts",
#                                           width=500,
#                                           height=400,
#                                           responsive=True,  # Make the plot responsive to the container size
#                                           dynamic=True,  # Enable dynamic range adjustment
#                                           )
#
# live_steprate_plot = df_stream.hvplot.bar(x='time', y='gStepcount_rate',
#                                           title="Live Stepcount Rate",
#                                           width=500,
#                                           height=400,
#                                           responsive=True,  # Make the plot responsive to the container size
#                                           dynamic=True,  # Enable dynamic range adjustment
#                                           )
#
# # Display the plot in a Panel layout
# live_stepcount_plot_pane = pn.pane.HoloViews(live_stepcount_plot)
# live_steprate_plot_pane = pn.pane.HoloViews(live_steprate_plot)

""" Responsive table """
step_table = step_pipeline.pipe(pn.widgets.Tabulator, pagination='remote', page_size=10,
                                sizing_mode='stretch_width')

# Define the styled title
# step_table_title = pn.pane.Markdown("**Activity Data Table**", style={'font-size': '30px'})
step_table_title = pn.pane.HTML("<div style='font-size: 30px; font-weight: bold;'>Activity Data Table</div>")


# def update_softmax(event=None):
#     number = pn.indicators.Number(
#         name='Probability', value=72, format='{value}%',
#         colors=[(33, 'green'), (66, 'gold'), (100, 'red')]
#     )
#     pn.Row(number.clone(value=float(pstate1)*100), number.clone(value=float(pstate2)*100), number.clone(value=float(pstate3)*100), number.clone(value=float(pstate4)*100))

"""  Indicator for probability softmax """
number = pn.indicators.Number(
    name='Probability', value=72, format='{value}%',
    colors=[(33, 'green'), (50, 'pink'), (100, 'red')]
)


# Simulate receiving gStepcount data from BLEHandler (this should come from BLE in practice)
def receive_gStepcount(gStepcount, gStepcount_rate):
    global time_index
    print("time_data:")
    print(time_data)
    time_data.append(time_index)  # Simulate time as index
    time_index = time_index+1
    #append_data(len(time_data), gStepcount)
    gStepcount_data.append(gStepcount)
    gStepcount_rate_data.append(gStepcount_rate)
    update_plot()

# Plotting function
def plot_gStepcount():
    global df_save
    if len(time_data) > 0:
        df_save = pd.DataFrame({'Time': list(time_data), 'gStepcount': list(gStepcount_data)})
        return df_save.hvplot(x='Time', y='gStepcount', title='Live Stepcount (Last 120 seconds)',
                             width=500, height=350)
    else:
        return hv.Curve([])  # Empty curve initially

def plot_gSteprate():
    if len(time_data) > 0:
        df = pd.DataFrame({'Time': list(time_data), 'gStepcount_rate': list(gStepcount_rate_data)})
        return df.hvplot.bar(x='Time', y='gStepcount_rate', title='Live Stepcount rate (Last 120 seconds)',
                             width=500, height=350)
    else:
        return hv.Curve([])  # Empty curve initially

# Callback function to update plot every time gStepcount updates
def update_plot(event=None):
    live_step_plot.object = plot_gStepcount()
    live_steprate_plot.object = plot_gSteprate()

# Initial empty plot
live_step_plot = pn.pane.HoloViews(plot_gStepcount(), width=500, sizing_mode='stretch_both')
live_steprate_plot = pn.pane.HoloViews(plot_gSteprate(), width=500, sizing_mode='stretch_both')

live_step_plot_title = pn.pane.HTML("<div style='font-size: 30EPG+Sensorpx; font-weight: bold;'>Live Cumulative Activity</div>")
live_steprate_plot_title = pn.pane.HTML("<div style='font-size: 30px; font-weight: bold;'>Live Activity</div>")

# def update_plot(event=None):
#     year_slider.value = int(gStepcount + 1750)
#
#     co2_pipeline = (
#         idf[
#             # (idf.year <= year_slider) &
#             (idf.year <= year_slider.value) &
#             (idf.country.isin(continents))
#             ]
#         .groupby(['country', 'year'])[yaxis_co2].mean()
#         .to_frame()
#         .reset_index()
#         .sort_values(by='year')
#         .reset_index(drop=True)
#     )
#     print(int(gStepcount+1750))
#     co2_plot.object = co2_pipeline.hvplot(x='year', by='country', y=yaxis_co2, line_width=2, title="CO2 emission by continent")
#
# #
# #
# co2_table = co2_pipeline.pipe(pn.widgets.Tabulator, pagination='remote', page_size=10, sizing_mode='stretch_width')

#
# co2_vs_gdp_scatterplot_pipeline = (
#     idf[
#         (idf.year == year_slider) &
#         (~ (idf.country.isin(continents)))
#         ]
#     .groupby(['country', 'year', 'gdp_per_capita'])['co2'].mean()
#     .to_frame()
#     .reset_index()
#     .sort_values(by='year')
#     .reset_index(drop=True)
# )




#
# co2_vs_gdp_scatterplot = co2_vs_gdp_scatterplot_pipeline.hvplot(x='gdp_per_capita',
#                                                                 y='co2',
#                                                                 by='country',
#                                                                 size=80, kind="scatter",
#                                                                 alpha=0.7,
#                                                                 legend=False,
#                                                                 height=500,
#                                                                 width=500)
#
# yaxis_co2_source = pn.widgets.RadioButtonGroup(
#     name='Y axis',
#     options=['coal_co2', 'oil_co2', 'gas_co2'],
#     button_type='success'
# )
#
# continents_excl_world = ['Asia', 'Oceania', 'Europe', 'Africa', 'North America', 'South America', 'Antarctica']
#
# co2_source_bar_pipeline = (
#     idf[
#         (idf.year == year_slider) &
#         (idf.country.isin(continents_excl_world))
#         ]
#     .groupby(['year', 'country'])[yaxis_co2_source].sum()
#     .to_frame()
#     .reset_index()
#     .sort_values(by='year')
#     .reset_index(drop=True)
# )
#
# co2_source_bar_plot = co2_source_bar_pipeline.hvplot(kind='bar',
#                                                      x='country',
#                                                      y=yaxis_co2_source,
#                                                      title='CO2 source by continent')


#
# # Create a Panel object for the plot
# co2_plot = pn.pane.HoloViews()

# event listener
#year_slider.param.watch(update_plot, 'value')  # so this is not necessary.....
#yaxis_co2.param.watch(update_plot, 'value')
# Create individual indicators for each posture with specific labels
prone_indicator = pn.indicators.Number(
    name='Prone', value=float(pstate1) * 100, format='{value}%',
    colors=[(33, 'green'), (66, 'gold'), (100, 'red')]
)
supine_indicator = pn.indicators.Number(
    name='Supine', value=float(pstate2) * 100, format='{value}%',
    colors=[(33, 'green'), (66, 'gold'), (100, 'red')]
)
stand2sit_indicator = pn.indicators.Number(
    name='Stand-to-sit', value=float(pstate3) * 100, format='{value}%',
    colors=[(33, 'green'), (66, 'gold'), (100, 'red')]
)
walking_indicator = pn.indicators.Number(
    name='Walk', value=float(pstate4) * 100, format='{value}%',
    colors=[(33, 'green'), (66, 'gold'), (100, 'red')]
)

fall_indicator = pn.indicators.Number(
    name='Fall', value=float(pstate5) * 100, format='{value}%',
    colors=[(33, 'green'), (66, 'gold'), (100, 'red')]
)

live_indicator_title = pn.pane.HTML("<div style='font-size: 30px; font-weight: bold;'>Live TensorflowLite Inference </div>")


save_button = pn.widgets.Button(name="💾 Save", width=100)



def save_to_csv(event):
    from datetime import datetime
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the file path
    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    # Create the file path with the timestamp
    file_name = f'step_data_{timestamp}.csv'
    file_path = os.path.join(current_dir, file_name)

    # Save the DataFrame to a CSV file
    df_save.to_csv(file_path, index=False)
    print(f"DataFrame saved to: {file_path}")

# Layout using Template
save_button.on_click(save_to_csv)


template = pn.template.FastListTemplate(
    title='Live Activity Dashboard',
    sidebar=[
        pn.pane.Markdown("# Live Input",  sizing_mode='stretch_width'),
             pn.pane.PNG('assets/eterna-ipg-front-shdw2-x400.png', sizing_mode='scale_both'),
             pn.pane.Markdown("## Settings"),
        time_slider],
    main=[
        pn.Row(
            pn.Column(
                # pn.Row(step_plot_title),
                pn.pane.Markdown("# Cumulative Activity"),
                pn.Row(step_plot.panel(sizing_mode='stretch_width'), margin=(0, 25)),
                # pn.Row(step_rate_plot_title),
                pn.pane.Markdown("# Activity Rate"),
                pn.Row(step_rate_plot.panel(sizing_mode='stretch_width'), margin=(0, 25))
            ),
            pn.Column(
                pn.pane.Markdown("# Activity History for Last 12 Min"),
                pn.Row(grid_static_plot_pane, sizing_mode='stretch_both', margin=(0, 25)),
                pn.pane.Markdown("# Activity Trend"),
                pn.Row(activity_trends_pane, sizing_mode='stretch_both', margin=(0, 25)),
            ),
        ),
        pn.Row(
            # pn.Column(step_table_title),
            pn.pane.Markdown("# Activity Data Table"),
            pn.Column(step_table.panel(width=500))),
        pn.Row(
            # pn.Row(live_indicator_title),
            pn.pane.Markdown("# Live TensorflowLite Inference "),
            pn.Row(prone_indicator, stand2sit_indicator,  supine_indicator, walking_indicator,
                   sizing_mode='stretch_width'),
        ),
        pn.Row(
            pn.Column(
                # pn.Row(live_step_plot_title),
                pn.pane.Markdown("# Live Cumulative Activity "),
                pn.Row(live_step_plot,  sizing_mode='stretch_both', margin=(0, 25)),
                # pn.Row(live_steprate_plot_title),
                pn.pane.Markdown("# Live Activity "),
                pn.Row(live_steprate_plot,  sizing_mode='stretch_both',margin=(0, 25))),
            pn.Column(
                # pn.Row(grid_plot_pane_title)
                pn.pane.Markdown("# Activity History for Last 12 min "),
                pn.Row(grid_plot_pane,  sizing_mode='stretch_both', margin=(0, 25)),  # Add the grid plot pane here
                pn.Row(image_displayer.image_pane, sizing_mode='stretch_both', margin=(0, 25))),
            ),
        pn.Row(
            save_button)
            # pn.Row(pn.Column("live Step Count", live_stepcount_plot_pane,  margin=(0, 25)),
            #        pn.Column("live Step Rate", live_steprate_plot_pane,  margin=(0, 25))),
          # pn.Row(pn.Column(co2_vs_gdp_scatterplot.panel(width=600), margin=(0, 25)),
          #        pn.Column(yaxis_co2_source, co2_source_bar_plot.panel(width=600)))

          ],

    accent_base_color="#88d8b0",
    header_background="#88d8b0",
)


# fix when initializing col in the main part:
# col = pn.Row(prone_indicator, supine_indicator, stand2sit_indicator, walking_indicator)
#
# col = pn.Row(number.clone(value=float(pstate1) * 100),
#              number.clone(value=float(pstate2) * 100),
#              number.clone(value=float(pstate3) * 100),
#              number.clone(value=float(pstate4) * 100))

# Append col to the template once initially
# template.main.append(col)


#    central_address = "5D:F4:6B:54:47:D8"  # Replace with your device's address (red watch)
central_address = "2E:4C:2A:C7:97:E5"  # Replace with your device's address (epg alternative)

# char_uuid = "00002a37-0000-1000-8000-00805f9b34fb"  # Replace with your characteristic's UUID
gesture_uuid = "00002a19-0000-1000-8000-00805f9b34fb"  # 2a19 is for battery level (used previously)
someother_uuid = "00002a18-0000-1000-8000-00805f9b34fb"  # for writing back

""" End of serial thread """
global gBLE_received
gBLE_received = False


gStepcount = 0




""" Global timer for sleep state """

# global_timer = QtCore.QTimer()
# global_timer.timeout.connect(flagpulse_timeout)
# global_timer.start(500)  # at every 500ms
global global_idle_count, gFree_fall_display_count
global_idle_count = 0  # initialize
gFree_fall_display_count = 0

""" Use Thread (backgroun?) to update GUI (asyncio can't handle GUI update) """
# Create a separate thread to run the BLE communication
global ble_thread, ble_1st_connection, gStepcount_offset
print("bottom")
ble_1st_connection = True
gStepcount_offset = 0
ble_thread = threading.Thread(target=lambda: asyncio.run(BLE_asyncThread()))
ble_thread.start()



## checking to see if the order after BLE matter: it does.
template.show()
template.servable();
