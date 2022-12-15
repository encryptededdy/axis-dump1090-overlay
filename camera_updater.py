import requests, json, time
from requests.auth import HTTPDigestAuth
from parse1090 import parse1090
import config
from turfpy.measurement import boolean_point_in_polygon
from geojson import Point, Polygon, Feature
import requests

last_set = None
counter = 0

def make_camera_request(string):
	jsonBody = {
	"apiVersion": "1.0",
	"method": "setText",
	"params": {
		"identity": 4,
		"text": string
	}
	}
	requests.post(config.camera1_overlay_url, json=jsonBody, auth=HTTPDigestAuth(config.camera1_username, config.camera1_pass))
	print(f"Set to {string}")

def update_camera(flight):
	global counter
	global last_set
	if flight is not None:
		ident = flight.ident
		altitude = flight.alt_geom
		last_set = ident
		make_camera_request(f"Aircraft ID\nCallsign: {ident}\nAltitude: {altitude}ft")
		counter = 0
	else:
		counter += 1
		if counter > 5 and last_set is not None:
			counter = 0
			make_camera_request("Aircraft ID\nNot Seen")
			last_set = None

def is_inside_poly(aircraft, poly):
	if not(isinstance(aircraft.lat, float) and isinstance(aircraft.lon, float)):
		return False
	ac_location = Feature(geometry=Point((aircraft.lat, aircraft.lon)))
	return boolean_point_in_polygon(ac_location, poly)


def find_flights(aircrafts):
	# Just checking 16R for now
	aircrafts_16r = list(filter(lambda x: is_inside_poly(x, config.syd_16r_land), parse1090.in_sky_and_ident(aircrafts)))
	if len(aircrafts_16r) > 1:
		aircrafts_16r.sort(key=lambda x:x.alt_baro)
	if len(aircrafts_16r) > 0:
		return aircrafts_16r[0]
	else:
		return None
	
while True:
	loop_start_time = time.time()
	aircraft = parse1090.parse_aircraft(config.adsb_url)
	# print(aircraft) 
	flight = find_flights(aircraft)
	update_camera(flight)
	# Prepare next loop
	loop_elapsed = time.time() - loop_start_time
	print(f"Loop took {loop_elapsed} seconds")
	time.sleep(max((config.interval - loop_elapsed), 0))
