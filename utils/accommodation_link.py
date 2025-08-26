from urllib.parse import quote_plus


def generate_airbnb_link(destination: str, check_in: str, check_out: str, num_adults: int) -> str:
    encoded_destination = quote_plus(destination)
    return (
        f"https://www.airbnb.com/s/homes?query={encoded_destination}"
        f"&checkin={check_in}&checkout={check_out}"
        f"&adults={num_adults}"
    )

def generate_booking_link(destination: str, check_in: str, check_out: str, num_adults: int) -> str:
    encoded_destination = quote_plus(destination)
    return (
        f"https://www.booking.com/searchresults.html?ss={encoded_destination}"
        f"&checkin={check_in}&checkout={check_out}"
        f"&group_adults={num_adults}"
    )

def generate_expedia_link(destination: str, check_in: str, check_out: str, num_adults: int) -> str:
    encoded_destination = quote_plus(destination)
    base = (
        f"https://www.expedia.com/Hotel-Search?destination={encoded_destination}"
        f"&checkIn={check_in}&checkOut={check_out}"
        f"&adults={num_adults}"
    )
    return base