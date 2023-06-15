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

class GarminActivity:
    CITIES = []
    STATES = []

    @classmethod
    def get_cities(cls):
        return cls.CITIES

    @classmethod
    def get_states(cls):
        return cls.STATES

    def __init__(self, time, points, activity_type="run"):
        self.activity_type = activity_type
        self.time = time
        self.points = points
        self.has_location = False

        if not hasattr(self, "_city"):
            self.parse_activity_data(points)

    def parse_activity_data(self, points):
        geolocator = Nominatim(user_agent="http")

        if points:
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

            state, city = self.get_location_by_coordinates(geolocator, self.center_lat, self.center_lon)
            if not city == '' or not state == '':
                self.has_location = True
                if not city == '':
                    self._city = city
                    print(f"City: {city}")
                    if not city in self.CITIES:
                        self.CITIES.append(city)
                if not state == '':
                    self._state = state
                    print(f"State: {state}")
                    if not state in self.STATES:
                        self.STATES.append(state)

    # def get_city(self):
    #     if hasattr(self, "_city"):
    #         return self._city
    
    def min_max(self):
        if self.has_location:
            return self.lat_minmax, self.long_minmax
        return None, None

    def get_location_by_coordinates(self, geolocator, lat, long):
        location = geolocator.reverse([lat, long])
        address = location.raw['address']

        # Extract the city from the address using alternative keys
        city = address.get('city', '') or address.get('town', '') or address.get('village', '') or ''
        state_province = address.get('state', '') or address.get('province', '') or ''
        return state_province, city

class FoliumMap:
    def __init__(self, center_lat=0, center_lon=0, zoom=2):
        self.center_lat = center_lat
        self.center_lon = center_lon
        self.zoom = zoom
        self.activity_points = []
        self.activities = []
    
    def make_map(self, state='None', city='None'):

        # If filtered by city or state
        if (not state == 'None' or not city == 'None') and len(self.activities) > 0:
            current_activities = []
            lat_minmax = [None, None]
            long_minmax = [None, None]
            for activity in self.activities:
                applied = False
                if hasattr(activity, "_city") and hasattr(activity, "_state"):
                    if (city in activity._city or not city) and (state in activity._state or not state):
                        current_activities.append(activity)
                        applied = True
                elif hasattr(activity, "_city"):
                    if city in activity._city() or not city:
                        current_activities.append(activity)
                        applied = True
                elif hasattr(activity, "_state"):
                    if state in activity._state() or not state:
                        current_activities.append(activity)
                        applied = True
                if applied:
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

        self._map = folium.Map(location=[self.center_lat, self.center_lon], zoom_start=self.zoom)
        self.draw_points()

    def access_map(self):
        if hasattr(self, "_map"):
            return self._map
        else:
            raise ValueError("Map hasn't been initialized yet")

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
                            lat = point.latitude
                            lon = point.longitude
                            # ele = point.elevation
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
        if hasattr(self, "_map"):
            self.save('{}.html'.format(mapName))
        else:
            raise ValueError("Map hasn't been initialized yet")

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

    print("Cities you ran in: ", GarminActivity.get_cities())
    print("States/Provinces you ran in: ", GarminActivity.get_states())

    vis_map.make_map(state=args.state, city=args.city)
    vis_map.save_map(args.state)