import gpxpy.gpx
import os
import glob
import folium
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time
import argparse
import imgkit
from math import log2, cos, pi
from geopy.geocoders import Nominatim

def get_location_by_coordinates(geolocator, lat, long):
    location = geolocator.reverse([lat, long])
    return location.address

class GarminActivity:
    def __init__(self, time, points, location=None, activity_type="run"):
        geolocator = Nominatim(user_agent="http")

        self.activity_type = activity_type
        self.time = time
        self.location = location
        self.points = points
        self.has_location = False

        if not location and points:
            latitudes = [point[0] for point in self.points]
            longitudes = [point[1] for point in self.points]

            # Calculate the center of the map
            self.lat_minmax = [min(latitudes), max(latitudes)]
            self.long_minmax = [min(longitudes), max(longitudes)]
            self.center_lat = (sum(self.lat_minmax)) / 2
            self.center_lon = (sum(self.long_minmax)) / 2

            # Calculate the distance between minimum and maximum coordinates
            lat_dist = max(latitudes) - min(latitudes)
            lon_dist = max(longitudes) - min(longitudes)

            # Calculate a reasonable zoom level based on the distance
            zoom_lat = int(log2(360 / lat_dist)) + 1
            zoom_lon = int(log2(360 / lon_dist / cos(pi * self.center_lat / 180))) + 1
            self.zoom = min(zoom_lat, zoom_lon)

            self.address = get_location_by_coordinates(geolocator, self.center_lat, self.center_lon)
            if len(self.address.split(",")) > 4:
                self.city_region = self.address.split(",")[-5].strip()
                self.state_prov = self.address.split(",")[-3].strip()
                self.has_location = True
            if len(self.address.split(",")) == 4:
                self.city_region = self.address.split(",")[-3].strip()
                self.state_prov = self.address.split(",")[-2].strip()
                self.has_location = True
            if len(self.address.split(",")) == 3:  
                self.city_region = self.address.split(",")[0].strip()
                self.state_prov = self.address.split(",")[1].strip()
                self.has_location = True
            if self.has_location:
                print(self.city_region)

    def state(self):
        if self.has_location:
            return self.state_prov
        return "None"
    
    def city(self):
        if self.has_location:
            return self.city_region
        return "None"
    
    def min_max(self):
        if self.has_location:
            return self.lat_minmax, self.long_minmax
        return None, None

class FoliumMap:
    def __init__(self, center_lat=0, center_lon=0, zoom=2):
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.zoom = zoom
        self.activity_points = []
        self.activities = []
    
    def make_map(self, state=None, city=None):
        if not state == 'None' and len(self.activities) > 0:
            current_activities = []
            current_points = []
            lat_minmax = [None, None]
            long_minmax = [None, None]
            for activity in self.activities:
                if state in activity.state():
                    current_activities.append(activity)
                    if lat_minmax[0] == None or lat_minmax[1] == None or long_minmax[0] == None or long_minmax[1] == None:
                        lat_minmax, long_minmax = activity.min_max()
                    else:
                        lat, long = activity.min_max()
                        if lat[0] < lat_minmax[0]:                    
                            lat_minmax[0] = lat[0]
                        if lat[1] > lat_minmax[1]:
                            lat_minmax[1] = lat[1]
                        if long[0] < long_minmax[0]:
                            long_minmax[0] = long[0] 
                        if long[1] > long_minmax[1]:
                            long_minmax[1] = long[1]

                if city in activity.city():
                    current_activities.append(activity)
                    if lat_minmax[0] == None or lat_minmax[1] == None or long_minmax[0] == None or long_minmax[1] == None:
                        lat_minmax, long_minmax = activity.min_max()
                    else:
                        lat, long = activity.min_max()
                        if lat[0] < lat_minmax[0]:                    
                            lat_minmax[0] = lat[0]
                        if lat[1] > lat_minmax[1]:
                            lat_minmax[1] = lat[1]
                        if long[0] < long_minmax[0]:
                            long_minmax[0] = long[0] 
                        if long[1] > long_minmax[1]:
                            long_minmax[1] = long[1]

            if not (lat_minmax[0] == None or lat_minmax[1] == None or long_minmax[0] == None or long_minmax[1] == None):
                self.center_lat = (sum(lat_minmax)) / 2
                self.center_lon = (sum(long_minmax)) / 2

                # Calculate the distance between minimum and maximum coordinates
                lat_dist = lat_minmax[1] - lat_minmax[0]
                lon_dist = long_minmax[1] - long_minmax[0]

                # Calculate a reasonable zoom level based on the distance
                zoom_lat = int(log2(360 / lat_dist)) + 1
                zoom_lon = int(log2(360 / lon_dist / cos(pi * self.center_lat / 180))) + 1
                self.zoom = min(zoom_lat, zoom_lon)

        self.map = folium.Map(location=[self.center_lat, self.center_lon], zoom_start=self.zoom)
        self.draw_points()

    def access_map(self):
        return self.map

    def load_data(self, gpx_path):
        # Find all .gpx files in the folder
        gpx_files = glob.glob(gpx_path + '/*.gpx')

        print("Loading data..")

        # Process each GPX file
        for file_path in gpx_files:
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
                            time = point.time
                            points.append((lat, lon))  # Append coordinates to the points list
    
                if len(points) > 2:
                    self.activity_points.append(points)

            if len(points) > 2:
                self.activities.append(GarminActivity(time, points))

        print("Loaded.")

    def draw_points(self):
        for activity in self.activity_points:
            folium.PolyLine(activity).add_to(self.map)

            # Add markers for the start and finish points
            start_point = folium.Marker(location=activity[0], popup='Start')
            start_point.add_to(self.map)
            end_point = folium.Marker(location=activity[-1], popup='Finish')
            end_point.add_to(self.map)
        
    def save_map(self, mapName="map"):
        self.map.save('{}.html'.format(mapName))

if __name__ == "__main__":
    # Training settings
    parser = argparse.ArgumentParser(description='Edge Segmentation')
    parser.add_argument('gpx_path', type=str, help='Path to config file')
    parser.add_argument('chromedriver_path', type=str, help='Path to config file')
    parser.add_argument('--state', type=str, default='None', help='Path to config file')
    parser.add_argument('--city', type=str, default='None', help='Path to config file')
    args = parser.parse_args()

    # Create the map object
    vis_map = FoliumMap()
    vis_map.load_data(args.gpx_path)

    vis_map.make_map(state=args.state, city=args.city)
    vis_map.save_map(args.state)