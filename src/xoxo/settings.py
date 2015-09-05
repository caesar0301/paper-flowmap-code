DEBUGGING = True

# Movement history
MOVEMENT_HIST = 'data/hcl.dat'

# Base station map
BSMAP = 'data/hcl_bm.dat'

# Max user number; for debugging
if DEBUGGING:
    MAX_USER_NUM = 100
else:
    MAX_USER_NUM = 1000000000