import gpxpy
import gpxpy.gpx
import os
import glob
import folium
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
from math import log2, cos, pi

gpx_path = r'C:\Users\jonat\Documents\Garmin\garmin-connect-export-master\garmin-connect-export-master\2022-07-18_garmin_connect_export'

chromedriver_path= r'C:\Users\jonat\Downloads\chromedriver_win32\chromedriver.exe'

# Find all .gpx files in the folder
gpx_files = glob.glob(gpx_path + '/*.gpx')

# Initialize the figure and axes for the animation
fig, ax = plt.subplots()

# Create the map object
map = folium.Map(location=[0, 0], zoom_start=2)

repo_path = r"C:\Users\jonat\Documents\Garmin_vis"

# Process each GPX file
def animate(i):
    file_path = gpx_files[i]
    print(file_path)
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        points = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    # Access individual data points (e.g., latitude, longitude, elevation, time)
                    lat = point.latitude
                    lon = point.longitude
                    ele = point.elevation
                    time_gar = point.time
                    points.append((lat, lon))  # Append coordinates to the points list

        # Extract latitude and longitude coordinates from points list\
        if len(points) <= 2:
            return

        latitudes = [point[0] for point in points]
        longitudes = [point[1] for point in points]

        # Calculate the center of the map
        center_lat = (min(latitudes) + max(latitudes)) / 2
        center_lon = (min(longitudes) + max(longitudes)) / 2

        # Calculate the distance between minimum and maximum coordinates
        lat_dist = max(latitudes) - min(latitudes)
        lon_dist = max(longitudes) - min(longitudes)

        # Calculate a reasonable zoom level based on the distance
        zoom_lat = int(log2(360 / lat_dist)) + 1
        zoom_lon = int(log2(360 / lon_dist / cos(pi * center_lat / 180))) + 1
        zoom = min(zoom_lat, zoom_lon)
        map = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)

        # Draw a polyline on the map
        folium.PolyLine(points).add_to(map)

        # Add markers for the start and finish points
        start_point = folium.Marker(location=points[0], popup='Start')
        start_point.add_to(map)
        end_point = folium.Marker(location=points[-1], popup='Finish')
        end_point.add_to(map)

        # Save the map as HTML
        # map.save('map_{}.html'.format(i))
        delay = 5
        fn = 'map_{}.html'.format(i)
        tmpurl = 'file://{path}/maps/{mapfile}'.format(path=os.getcwd(), mapfile=fn)
        map.save(os.path.join("maps",fn))

        service = Service(chromedriver_path)
        browser = webdriver.Chrome(executable_path=chromedriver_path, service=service)
        browser.get(tmpurl)
        # Give the map tiles some time to load
        time.sleep(delay)
        browser.save_screenshot('maps/map_{}.png'.format(i))
        browser.quit()

        # Read the saved map HTML file
        html_map = open('maps/map_{}.png'.format(i), 'rb').read()

        # Clear the previous plot
        ax.clear()

        # Display the map as an image on the plot
        ax.imshow(plt.imread('maps/map_{}.png'.format(i), format='png'))

        # Set the aspect ratio and limits for the plot
        ax.set_aspect('auto')
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)

# Create the animation
ani = animation.FuncAnimation(fig, animate, frames=len(gpx_files), interval=2000)

# Save the animation as a video
ani.save('animation.mp4', writer='ffmpeg')

print("Saved video")
