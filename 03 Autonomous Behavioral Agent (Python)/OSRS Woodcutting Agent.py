#libraries used are autopygui (for mouse control), Pillow (image processing), and OpenCV (Open Source Computer Vision)
import os
import pyautogui
import time
import random


script_dir = os.path.dirname(__file__)

def reset():
    reset_tile = os.path.join(script_dir, 'reset_tile.png')
    
    
    try:
        location = pyautogui.locateCenterOnScreen(reset_tile, confidence = 0.3)
        if location is not None:
            reset_x, reset_y = location

            # making the click a little random to avoid bot detection
            reset_x += random.randrange(-2, 2) 
            reset_y += random.randrange(-2, 2)

            pyautogui.moveTo(reset_x, reset_y, 0.5, pyautogui.easeInQuad)
            pyautogui.click()
            time.sleep(random.uniform(2, 3))
            return
    except pyautogui.ImageNotFoundException:
        pass # try next confidence level
    
    print("Reset tile not found at any confidence level.")


def check_inventory():
    inventory_full = os.path.join(script_dir, 'inventory_full.png')

    try:
        check_inventory_location = pyautogui.locateOnScreen(inventory_full, confidence = 0.6) 
        if check_inventory_location is not None:
            return True
    
    except pyautogui.ImageNotFoundException:
        return


def bank_items():
    bank = os.path.join(script_dir, 'bank.png')
    logs = os.path.join(script_dir, 'logs.png')
    bank_exit = os.path.join(script_dir, 'bank_exit.png')
    trees_bank_reset = os.path.join(script_dir, 'trees_bank_reset.png')

    for confidence in (0.8, 0.5, 0.3):
        try:    
            bank_location = pyautogui.locateCenterOnScreen(bank, confidence = confidence)    
            if bank_location is not None:
                bank_x, bank_y = bank_location
                
                # making the click a little random to avoid bot detection
                bank_x += random.randrange(-2, 2) 
                bank_y += random.randrange(-2, 2)

                pyautogui.moveTo(bank_x, bank_y, .4, pyautogui.easeOutQuad)
                pyautogui.click()
                time.sleep(random.uniform(9, 10))

                logs_location = pyautogui.locateCenterOnScreen(logs, region=(1508, 442, 360, 500), confidence = 0.7)
                if logs_location is not None:
                    logs_x, logs_y = logs_location
                    logs_x += random.randrange(-2, 2) #bot detection avoidance
                    logs_y += random.randrange(-2, 2) #bot detection avoidance

                    pyautogui.moveTo(logs_x, logs_y, .4, pyautogui.easeInQuad)
                    pyautogui.click()
                    time.sleep(random.uniform(0, 1))

                else:
                    break

                bank_exit_location = pyautogui.locateCenterOnScreen(bank_exit, confidence = 0.7)
                if bank_exit_location is not None:
                    bank_exit_x, bank_exit_y = bank_exit_location
                    bank_exit_x += random.randrange(-2, 2) #bot detection avoidance
                    bank_exit_y += random.randrange(-2, 2) #bot detection avoidance

                    pyautogui.moveTo(bank_exit_x, bank_exit_y, .4, pyautogui.easeInQuad)
                    pyautogui.click()
                    time.sleep(random.uniform(0, 1))

                else:
                    break

                #screen rotation to see trees
                pyautogui.keyDown('left')
                time.sleep(1)
                pyautogui.keyUp('left')
                time.sleep(1)

                trees_bank_reset_location = pyautogui.locateCenterOnScreen(trees_bank_reset, confidence = 0.7)
                if trees_bank_reset_location is not None:
                    trees_bank_reset_x, trees_bank_reset_y = trees_bank_reset_location
                    trees_bank_reset_x += random.randrange(-2, 2) #bot detection avoidance
                    trees_bank_reset_y += random.randrange(-2, 2) #bot detection avoidance

                    pyautogui.moveTo(trees_bank_reset_x, trees_bank_reset_y, .4, pyautogui.easeInQuad)
                    pyautogui.click()
                    time.sleep(random.uniform(9, 10))

                else:
                    break

                #moving screen to original orientation
                pyautogui.keyDown('right')
                time.sleep(1)
                pyautogui.keyUp('right')

                reset()
                return



        except pyautogui.ImageNotFoundException:
            reset()        

    print("Bank not found at any confidence level.")
                

def woodcutting():
    trees = [
            os.path.join(script_dir, f'tree_{i}.png') for i in range (1, 2)
    ]
    
    for tree in trees:
        try:    
            tree_location = pyautogui.locateCenterOnScreen(tree, confidence = 0.6)    
            if tree_location is not None:
                tree_x, tree_y = tree_location
                
                # making the click a little random to avoid bot detection
                tree_x += random.randrange(-2, 2) 
                tree_y += random.randrange(-2, 2)

                pyautogui.moveTo(tree_x, tree_y, .4, pyautogui.easeOutQuad)
                pyautogui.click()
                time.sleep(5)
                if check_inventory() is True:
                    bank_items()
                else:
                    time.sleep(random.uniform(30, 31))
                
                reset()
                break
        
        except pyautogui.ImageNotFoundException:
            pass
    
    else:
        reset()
  

if __name__ == "__main__":
    time.sleep(1)
    
    while True:       
        woodcutting()     
        time.sleep(0.1)  #Making sure that it doesn't run so fast that it overloads my CPU
        
        
