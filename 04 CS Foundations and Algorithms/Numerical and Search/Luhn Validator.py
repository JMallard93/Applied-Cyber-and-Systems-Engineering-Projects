def verify_card_number(card_number):
    # reversing the card number into a list of numbers, removing spaces, dashes, and the check digit
    card_number = str(card_number)
    reversed_number = card_number[::-1]
    digits = [int(digit) for digit in reversed_number if digit.isdigit()]
    # storing, then removing the check digit
    check_digit = digits[0]
    del digits[0]
    # identifying every other digit
    odd_digits = digits[::2]
    even_digits = digits[1::2]
   
    modified_odd_digits = []
    for digit in odd_digits:
        digit *= 2
        if digit > 9:
            digit -= 9
        modified_odd_digits.append(digit)
   
   
    # putting everything back together
    modified_digits = modified_odd_digits + even_digits
    modified_digits.append(check_digit)

    sum_of_digits = sum(modified_digits)
       

    if sum_of_digits % 10 == 0:
        return "VALID!"
    else:
        return "INVALID!"

   

print(verify_card_number("1234-643"))
