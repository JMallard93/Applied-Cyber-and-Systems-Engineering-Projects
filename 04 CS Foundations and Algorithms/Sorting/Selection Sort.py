def selection_sort(int_list):
    for i in range(len(int_list)):
        smallest = i
       
        for j in range(i + 1, len(int_list)):
            if int_list[smallest] > int_list[j]:
                smallest = j

        if smallest != i:
            int_list[i], int_list[smallest] = int_list[smallest], int_list[i]

    return int_list
