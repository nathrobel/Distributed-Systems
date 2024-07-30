#!/usr/bin/python3

import reservationapi
import configparser
import logging

# Load the configuration file containing the URLs and keys
config = configparser.ConfigParser()
config.read("api.ini")

# Create an API object to communicate with the hotel API
hotel  = reservationapi.ReservationApi(config['hotel']['url'],
                                       config['hotel']['key'],
                                       int(config['global']['retries']),
                                       float(config['global']['delay']))



# Your code goes here
# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def view_slots_available(hotel):
    try:
        hotel_slots = hotel.get_slots_available()

        print("Available Hotel Slots:")
        print(hotel_slots)

    except Exception as e:
        logging.error(f"An error occurred when fetching available slots: {str(e)}")


def view_slots_held(hotel):
    try:
        hotel_booked_slots = hotel.get_slots_held()
       
        print("Held Hotel Slots:")
        print(hotel_booked_slots)


    except Exception as e:
        logging.error(f"An error occurred when fetching available slots: {str(e)}")


def release_slot(hotel):
    try:
        # Fetch held slots for the hotel
        hotel_booked_slots = hotel.get_slots_held()
       
        # Check if there are held slots
        if not hotel_booked_slots:
            print("No bookings to release for hotel.")
            return

        # Release all held slots for the hotel
        for slot in hotel_booked_slots:
            if hotel.release_slot(slot['id']):
                print(f"Successfully released slot {slot['id']} for hotel.")
            else:
                print(f"Failed to release slot {slot['id']} for hotel.")

    except Exception as e:
        logging.error(f"An error occurred while releasing slots: {str(e)}")




def make_reservation(hotel):
    try:
        available_slots = hotel.get_slots_available()

        if len(available_slots) < 2:
            print("Not enough available slots for hotel.")
            return

        # Choose the first two available slots automatically
        slot_id_1 = available_slots[0]['id']
        slot_id_2 = available_slots[1]['id']

        # Attempt to reserve the chosen slots
        if hotel.reserve_slot(slot_id_1) and hotel.reserve_slot(slot_id_2):
            print(f"Successfully reserved slots {slot_id_1} and {slot_id_2} for hotel.")
        else:
            print(f"Failed to reserve slots {slot_id_1} and {slot_id_2} for hotel.")

    except Exception as e:
        logging.error(f"An error occurred during reservation: {str(e)}")



if __name__ =='__main__':

    view_slots_available(hotel)
    make_reservation(hotel)
    view_slots_held(hotel)
    release_slot(hotel)
    view_slots_held(hotel)
