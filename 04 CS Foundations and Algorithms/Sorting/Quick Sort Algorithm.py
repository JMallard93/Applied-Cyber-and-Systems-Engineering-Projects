def quick_sort(int_list):
    if int_list == []:
        return []
   
    pivot = int_list[0]

    lessthan_pivot = []
    morethan_pivot = []
    equalto_pivot = []

    for number in int_list:
        if number < pivot:
            lessthan_pivot.append(number)
        if number > pivot:
            morethan_pivot.append(number)
        if number == pivot:
            equalto_pivot.append(number)

    sorted_lessthan_pivot = quick_sort(lessthan_pivot)
    sorted_morethan_pivot = quick_sort(morethan_pivot)

    return sorted_lessthan_pivot + equalto_pivot + sorted_morethan_pivot
       
print(quick_sort([4, 42, 16, 23, 15, 8]))
