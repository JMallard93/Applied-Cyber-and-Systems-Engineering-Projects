#finding the square root of a number via bisection
def square_root_bisection(number, error_margin = .01, max_iterations = 20):
    if number < 0:
        raise ValueError("Square root of negative number is not defined in real numbers")
    elif number == 0 or number == 1:
        print(f"The square root of {number} is {number}")
        return number
   


    low = 0
   
    if number > 0 and number < 1:
        high = 1
    else:
        high = number
   
    attempts = 0

    while (high - low) > error_margin:  
        mid = (high + low) / 2    
        if mid ** 2 == number:
            # we have our answer, now we need to break out of the while loop while remaining in the function
            break
        elif (mid ** 2) > number:
            high = mid
            attempts += 1
        elif (mid ** 2) < number:
            low = mid
            attempts += 1
       
        if attempts >= max_iterations:
            print(f"Failed to converge within {max_iterations} iterations")
            return None

    root = mid
    square_target = number

    print(f"The square root of {square_target} is approximately {root}")
    return root
