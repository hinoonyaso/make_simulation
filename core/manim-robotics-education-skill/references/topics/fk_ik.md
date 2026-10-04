# FK / IK

## FK visual chain
joint angle change -> link rotates about its visible axis -> child frame moves with the link -> end-effector pose updates -> equation terms are introduced from that geometry.
Keep one arm on screen. Do not replace it with a new diagram for each equation.

For planar teaching, show one link first, then add the second link. Build `theta1`, then relative `theta2`, then the accumulated orientation `theta1+theta2`. Copy visible horizontal/vertical projections into the x/y equations.

## IK
Show target pose separately from achieved pose. Solver output changes joint values; final achieved/error is measured. Do not imply MoveIt2 or a numerical solver unless actually used.
