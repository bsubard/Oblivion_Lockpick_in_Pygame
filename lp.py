import pygame
import sys
import random

# --- Configuration Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

BACKGROUND_COLOR = WHITE
RECT_COLOR = BLUE
CEILING_COLOR = BLACK
SUCCESS_TEXT_COLOR = GREEN
FAILURE_TEXT_COLOR = RED
DEBUG_TEXT_COLOR = BLACK

# Moving Rectangle properties
RECT_WIDTH = 100
RECT_HEIGHT = 50

# Rise properties
MIN_RISE_DISTANCE_FROM_BOTTOM = 100
MAX_RISE_DISTANCE_FROM_BOTTOM = 100 

MIN_RISE_SPEED_PIXELS_PER_FRAME = 3
MAX_RISE_SPEED_PIXELS_PER_FRAME = 6 
MIN_TOP_HOLD_MS = 50
MAX_TOP_HOLD_MS = 200
GRAVITY_PIXELS_PER_FRAME = 3

# Ceiling Rectangle Properties
CEILING_RECT_HEIGHT = 10
CEILING_RECT_WIDTH = RECT_WIDTH + 20

# --- Initialize Pygame ---
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Timing Game")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# --- Calculate Initial/Fixed Positions ---
bottom_y_position_rect_top = SCREEN_HEIGHT - RECT_HEIGHT - 20
ceiling_rect_x = (SCREEN_WIDTH - CEILING_RECT_WIDTH) // 2

# --- Game State Variables ---
rect_x = (SCREEN_WIDTH - RECT_WIDTH) // 2
rect_y = bottom_y_position_rect_top
rect_object = pygame.Rect(rect_x, rect_y, RECT_WIDTH, RECT_HEIGHT)
ceiling_rect_obj = pygame.Rect(ceiling_rect_x, 0, CEILING_RECT_WIDTH, CEILING_RECT_HEIGHT) # Y will be set

current_state = "IDLE"
time_reached_top = 0
current_top_hold_duration_ms = 0 # Active hold duration when AT_TOP
current_rise_speed = 0           # Active rise speed when RISING

# Challenge-specific variables (these persist until a spacebar press that resets challenge)
current_challenge_target_y = 0 # The target Y for the top of the blue rect for the current challenge
current_challenge_ceiling_y = 0 # The Y for the top of the ceiling for the current challenge

# Parameters for the current ascent attempt
# These are set when an ascent starts from IDLE.
# If a fall is interrupted, these values from the previous ascent (that led to the fall) are reused.
attempt_rise_speed = 0
attempt_top_hold_duration = 0 # This is the *intended* hold duration for the current ascent if it reaches the top

# Active rise variable (for the current ascent motion's target)
active_target_y_for_current_rise = 0

success_count = 0
failure_count = 0

# --- Helper Function to Set New Challenge Height ---
def initialize_new_challenge():
    global current_challenge_target_y, current_challenge_ceiling_y, ceiling_rect_obj
    # Note: Rise speed and hold duration for an *attempt* are NOT set here.
    # They are set when an attempt begins from IDLE state.

    random_rise_distance = random.randint(MIN_RISE_DISTANCE_FROM_BOTTOM, MAX_RISE_DISTANCE_FROM_BOTTOM)
    
    current_challenge_target_y = bottom_y_position_rect_top - random_rise_distance
    if current_challenge_target_y < 0:
        current_challenge_target_y = 0 # Ensure it doesn't go above the screen
    
    current_challenge_ceiling_y = current_challenge_target_y - CEILING_RECT_HEIGHT
    ceiling_rect_obj.y = current_challenge_ceiling_y # Update ceiling's actual Y position

    #print(f"NEW CHALLENGE: TargetY: {current_challenge_target_y}, CeilingY: {ceiling_rect_obj.y}")

# Initialize the very first challenge
initialize_new_challenge()

# --- Game Loop ---
running = True
while running:
    current_time_ms = pygame.time.get_ticks()

    # --- Event Handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                if current_state == "IDLE":
                    # Start a new ascent attempt for the current challenge target.
                    # New speed and hold duration are generated for this attempt.
                    attempt_rise_speed = random.randint(MIN_RISE_SPEED_PIXELS_PER_FRAME, MAX_RISE_SPEED_PIXELS_PER_FRAME)
                    attempt_top_hold_duration = random.randint(MIN_TOP_HOLD_MS, MAX_TOP_HOLD_MS)
                    
                    current_rise_speed = attempt_rise_speed # Set active rise speed
                    active_target_y_for_current_rise = current_challenge_target_y
                    ceiling_rect_obj.y = current_challenge_ceiling_y # Ensure ceiling is visually correct
                    
                    current_state = "RISING"
                    #print(f"State: {current_state} (from IDLE). TargetY: {active_target_y_for_current_rise}, RiseSpeed: {current_rise_speed}, IntendedHold: {attempt_top_hold_duration/1000.0:.2f}s")

                elif current_state == "FALLING":
                    # Interrupting a fall. Reuse the parameters from the ascent that led to this fall.
                    # attempt_rise_speed and attempt_top_hold_duration still hold values from that ascent.
                    
                    current_rise_speed = attempt_rise_speed # Reuse stored rise speed
                    active_target_y_for_current_rise = current_challenge_target_y # Target Y is still the same
                    ceiling_rect_obj.y = current_challenge_ceiling_y 
                    
                    current_state = "RISING"
                    #print(f"State: {current_state} (from FALLING). TargetY: {active_target_y_for_current_rise}, RiseSpeed: {current_rise_speed}, IntendedHold: {attempt_top_hold_duration/1000.0:.2f}s (reused)")


            if event.key == pygame.K_SPACE:
                reset_and_new_challenge = False 

                if current_state == "AT_TOP":
                    if current_time_ms - time_reached_top <= current_top_hold_duration_ms:
                        success_count += 1
                        #print("SUCCESS! Space pressed in time.")
                    else:
                        failure_count += 1
                        #print(f"FAILURE! Space pressed too late (AT_TOP).")
                    reset_and_new_challenge = True

                elif current_state == "FALLING":
                    failure_count += 1
                    #print("FAILURE! Space pressed while FALLING.")
                    reset_and_new_challenge = True

                elif current_state == "RISING":
                    failure_count +=1
                    #print("FAILURE! Space pressed while RISING.")
                    reset_and_new_challenge = True
                
                if reset_and_new_challenge:
                    rect_object.y = bottom_y_position_rect_top
                    current_state = "IDLE"
                    initialize_new_challenge() # Set new target Y for the next challenge.
                                               # Rise speed/hold for the *next attempt* will be set on next K_UP from IDLE.


    # --- Game Logic / State Updates ---
    if current_state == "RISING":
        rect_object.y -= current_rise_speed
        if rect_object.y <= active_target_y_for_current_rise:
            rect_object.y = active_target_y_for_current_rise # Snap to exact position
            current_state = "AT_TOP"
            time_reached_top = current_time_ms
            # Set the active hold duration using the one determined for this ascent attempt
            current_top_hold_duration_ms = attempt_top_hold_duration
            #print(f"State: {current_state}. Reached top at Y: {rect_object.y}. Hold for: {current_top_hold_duration_ms/1000.0:.2f}s")

    elif current_state == "AT_TOP":
        if current_time_ms - time_reached_top > current_top_hold_duration_ms:
            # Hold time expired without a space press.
            current_state = "FALLING"
            #print(f"State: {current_state}. Hold time expired. No timely space press.")
            # attempt_rise_speed and attempt_top_hold_duration remain unchanged,
            # so if K_UP is pressed during FALLING, they will be reused.

    elif current_state == "FALLING":
        rect_object.y += GRAVITY_PIXELS_PER_FRAME
        if rect_object.y >= bottom_y_position_rect_top:
            rect_object.y = bottom_y_position_rect_top # Snap to bottom
            current_state = "IDLE"
            #print(f"State: {current_state}. Reached bottom. Challenge height remains.")
            # If K_UP is pressed now, new attempt_rise_speed and attempt_top_hold_duration will be generated.

    # --- Drawing ---
    screen.fill(BACKGROUND_COLOR)
    pygame.draw.rect(screen, CEILING_COLOR, ceiling_rect_obj)
    pygame.draw.rect(screen, RECT_COLOR, rect_object)

    success_text = font.render(f"Success: {success_count}", True, SUCCESS_TEXT_COLOR)
    failure_text = font.render(f"Failure: {failure_count}", True, FAILURE_TEXT_COLOR)
    screen.blit(success_text, (10, 10))
    screen.blit(failure_text, (10, 50))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
