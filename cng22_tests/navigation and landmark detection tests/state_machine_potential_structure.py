#potential structure for state machine architecture
#proved too difficult to implement


'''state = do_nothing_state

while True:
    # get video frame into frame variable
    state(frame)

def do_nothing_state(frame):
    # clever image processing
    if should_keep_doing_nothing:
        return

    if can_see_square:
        state = tipping_forward_state
        send_tip_forward()
        return

def tipping_forward_state(frame):
    # clever image processing
    if square_too_close:
        pass
'''
