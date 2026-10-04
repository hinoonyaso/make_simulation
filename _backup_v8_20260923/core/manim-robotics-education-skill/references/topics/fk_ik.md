# FK / IK
FK: joint vector -> chained transforms -> end-effector pose. IK: target pose -> solver -> joint solution -> achieved pose/error. Separate target from achieved state; do not imply MoveIt2 unless actually used.
