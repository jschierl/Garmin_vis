import gpxpy
import gpxpy.gpx
import os
import glob
import folium
import argparse

def save_map(gpx_path):
    # Create the map object
    map = folium.Map(location=[0, 0], zoom_start=2)

    # Find all .gpx files in the folder
    gpx_files = glob.glob(gpx_path + '/*.gpx')

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

            # Draw a polyline on the map
            if len(points) > 2:
                folium.PolyLine(points).add_to(map)

                # Add markers for the start and finish points
                start_point = folium.Marker(location=points[0], popup='Start')
                start_point.add_to(map)
                end_point = folium.Marker(location=points[-1], popup='Finish')
                end_point.add_to(map)

    # Save the map as HTML
    map.save('map.html')
    print("Saved map")

if __name__ == "__main__":
    # Training settings
    parser = argparse.ArgumentParser(description='Edge Segmentation')
    parser.add_argument('gpx_path', type=str, help='Path to config file')
    args = parser.parse_args()

    save_map(args.gpx_path)