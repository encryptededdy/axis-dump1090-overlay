import requests, json, time
from requests.auth import HTTPDigestAuth
from parse1090 import parse1090
import config
from turfpy.measurement import boolean_point_in_polygon
from geojson import Point, Polygon, Feature
import requests

last_set = None

def make_camera_request_1(string):
	jsonBody = {
	"apiVersion": "1.0",
	"method": "setText",
	"params": {
		"camera": 1,
		"identity": 5,
		"text": string
	}
	}
	requests.post(config.camera1_overlay_url, json=jsonBody, auth=HTTPDigestAuth(config.camera1_username, config.camera1_pass))
	print(f"Set to {string}")

def make_camera_request_2(string):
	jsonBody = {
	"apiVersion": "1.0",
	"method": "setText",
	"params": {
		"camera": 1,
		"identity": 3,
		"text": string
	}
	}
	requests.post(config.camera2_overlay_url, json=jsonBody, auth=HTTPDigestAuth(config.camera2_username, config.camera2_pass))
	print(f"Set 2 to {string}")

def is_inside_poly_max_alt(aircraft, poly, max_alt):
	if not(isinstance(aircraft.lat, float) and isinstance(aircraft.lon, float)):
		return False
	ac_location = Feature(geometry=Point((aircraft.lon, aircraft.lat)))
	return boolean_point_in_polygon(ac_location, poly) and (aircraft.alt_baro == "ground" or int(aircraft.alt_baro) < max_alt)


def find_flight_34L(aircrafts):
	aircrafts_34l = list(filter(lambda x: is_inside_poly_max_alt(x, config.syd_34L, 1000), parse1090.with_ident(aircrafts, True)))
	if len(aircrafts_34l) > 1:
		aircrafts_34l.sort(key=lambda x:x.lat) # southernmost should be first, as it's aesc
	if len(aircrafts_34l) > 0:
		return f"{aircrafts_34l[0].ident.rstrip()} ({aircrafts_34l[0].alt_baro}ft)"
	else:
		return ""
	
def find_flight_16L(aircrafts):
	aircrafts_16l = list(filter(lambda x: is_inside_poly_max_alt(x, config.syd_16L, 1000), parse1090.with_ident(aircrafts, True)))
	if len(aircrafts_16l) > 1:
		aircrafts_16l.sort(key=lambda x:x.lat) # southernmost should be first, as it's aesc
	if len(aircrafts_16l) > 0:
		return f"{aircrafts_16l[0].ident.rstrip()} ({aircrafts_16l[0].alt_baro}ft)"
	else:
		return ""
	
def find_flight_taxiway(aircrafts):
	aircrafts_taxi = list(filter(lambda x: is_inside_poly_max_alt(x, config.syd_taxi_alpha, 1000), parse1090.with_ident(aircrafts, True)))
	aircrafts_taxi.sort(key=lambda x:x.lat) # southernmost should be first, as it's aesc
	if len(aircrafts_taxi) > 0:
		return ", ".join(str(x.ident.rstrip()) for x in aircrafts_taxi)
	else:
		return ""

def find_flight_25_final(aircrafts):
	aircrafts_25 = list(filter(lambda x: is_inside_poly_max_alt(x, config.syd_25_approach, 1000), parse1090.with_ident(aircrafts, True)))
	if len(aircrafts_25) > 1:
		aircrafts_25.sort(key=lambda x:x.alt_baro) # lowest should be first, as it's aesc
	if len(aircrafts_25) > 0:
		return f"{aircrafts_25[0].ident.rstrip()} ({aircrafts_25[0].alt_baro}ft)"
	else:
		return ""
	
while True:
	loop_start_time = time.time()
	try:
		aircraft = parse1090.parse_aircraft(config.adsb_url)
		# force 15char to reduce flickering on resize
		string_34l = find_flight_34L(aircraft).ljust(15)
		string_16l = find_flight_16L(aircraft).ljust(15)
		string_taxi = find_flight_taxiway(aircraft).ljust(15)
		string_25 = find_flight_25_final(aircraft).ljust(15)
		combined_str_cam1 = f"{string_taxi}\n{string_34l}\n{string_16l}\n{string_25}"
		combined_str_cam2 = f"{string_taxi}\n{string_34l}\n{string_16l}"
	except:
		combined_str_cam1 = "dump1090\nerror\n:("
		combined_str_cam2 = "dump1090\nerror\n:("
	# print(aircraft) 
	if combined_str_cam1 != last_set:
		make_camera_request_1(combined_str_cam1)
		make_camera_request_2(combined_str_cam2)
		last_set = combined_str_cam1
	# Prepare next loop
	loop_elapsed = time.time() - loop_start_time
	print(f"Loop took {loop_elapsed} seconds")
	time.sleep(max((config.interval - loop_elapsed), 0))
