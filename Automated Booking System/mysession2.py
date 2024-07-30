import time
import logging
import reservationapi
import configparser

# Load the configuration file containing the URLs and keys
config = configparser.ConfigParser()
config.read("api.ini")

# Create an API object to communicate with the hotel and band APIs
hotel = reservationapi.ReservationApi(config['hotel']['url'],
                                      config['hotel']['key'],
                                      int(config['global']['retries']),
                                      float(config['global']['delay']))

band = reservationapi.ReservationApi(config['band']['url'],
                                     config['band']['key'],
                                     int(config['global']['retries']),
                                     float(config['global']['delay']))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clear_existing_bookings(api, api_name):
    try:
        booked_slots = api.get_slots_held()
        for slot in booked_slots:
            api.release_slot(slot['id'])
            logging.info(f"Released existing slot {slot['id']} for {api_name}")
    except Exception as e:
        logging.error(f"Error releasing slots for {api_name}: {str(e)}")


def check_common_slots(hotel, band):
    try:
        hotel_slots = [slot['id'] for slot in hotel.get_slots_available()]
        band_slots = [slot['id'] for slot in band.get_slots_available()]
        common_slots = list(set(hotel_slots).intersection(band_slots))
        common_slots = sorted(common_slots)[:20]  # Limit to first 20 common slots
        logging.info("First 20 Common Slots:")
        for slot in common_slots:
            logging.info(f"Slot ID: {slot}")
        return common_slots
    except Exception as e:
        logging.error(f"An error occurred when fetching common slots: {str(e)}")

def book_earliest_common_slot(hotel, band, common_slots):
    try:
        if not common_slots:
            logging.info("No common slots available.")
            return None
        for slot in common_slots[:2]:  # Limit to the earliest 2 slots available
            hotel_response = hotel.reserve_slot(slot)
            band_response = band.reserve_slot(slot)
            if hotel_response and band_response:
                logging.info(f"Successfully reserved slot {slot} for both hotel and band.")
            else:
                logging.error(f"Failed to reserve slot {slot} for both hotel and band.")
                return None
        return common_slots[:2]
    except Exception as e:
        logging.error(f"An error occurred during reservation: {str(e)}")


def recheck_for_better_bookings(hotel, band, booked_slots):
    try:
        time.sleep(1)
        new_common_slots = check_common_slots(hotel, band)
        if not new_common_slots:
            logging.info("No better common slots available.")
            return booked_slots

        # Sort new common slots and get the earliest available slots
        new_earliest_slots = sorted(new_common_slots)
        booked_sorted = sorted(booked_slots)

        # Identify new slots that are earlier than the earliest booked slot
        better_slots = [slot for slot in new_earliest_slots if slot < booked_sorted[0]]

        if len(better_slots) == 0:
            logging.info("No earlier slots available.")
            return booked_slots
        elif len(better_slots) == 1:
            logging.info("1 earlier slot available.")
            # Replace the latest booked slot with the new earlier slot
            slot_to_book = better_slots[0]
            slot_to_release = booked_sorted[-1]

            # Process to release and book the new slot
            hotel.release_slot(slot_to_release)
            band.release_slot(slot_to_release)
            logging.info(f"Released slot {slot_to_release}")

            if hotel.reserve_slot(slot_to_book) and band.reserve_slot(slot_to_book):
                logging.info(f"Successfully booked slot {slot_to_book}")
                return [booked_sorted[0], slot_to_book] if booked_sorted[0] < slot_to_book else [slot_to_book, booked_sorted[0]]
            else:
                logging.error(f"Failed to book slot {slot_to_book}")
                return booked_slots
        elif len(better_slots) >= 2:
            logging.info("2 earlier slots available.")
            slots_to_book = better_slots[:2]  # Take the two earliest new slots
            slots_to_release = booked_sorted  # Release both currently booked slots

            # Release old slots
            for slot in slots_to_release:
                hotel.release_slot(slot)
                band.release_slot(slot)
                logging.info(f"Released slot {slot}")

            # Book new slots
            booked_new_slots = []
            for slot in slots_to_book:
                if hotel.reserve_slot(slot) and band.reserve_slot(slot):
                    booked_new_slots.append(slot)
                    logging.info(f"Successfully booked slot {slot}")
                else:
                    logging.error(f"Failed to book slot {slot}")

            return booked_new_slots if len(booked_new_slots) == 2 else booked_slots

    except Exception as e:
        logging.error(f"An error occurred during recheck for better bookings: {str(e)}")
        return booked_slots




if __name__ == '__main__':
    clear_existing_bookings(hotel,"hotel")
    clear_existing_bookings(band,"band")

    common_slots = check_common_slots(hotel, band)
    if common_slots:
        booked_slots = book_earliest_common_slot(hotel, band, common_slots)
        if booked_slots:
            final_slots = recheck_for_better_bookings(hotel, band, booked_slots)
            logging.info(f"Successfully booked the following slots: {final_slots}")