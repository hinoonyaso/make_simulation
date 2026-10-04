# FK / IK

Use one reusable arm object with visible joint axes. Prefer state keyframes/trace playback over spawning new arms. Auto-frame the active links/end-effector before manual camera tuning.

FK: joint state -> chained transforms -> end-effector frame. Ghost only the previous/target pose when comparison helps; avoid multiple opaque arms competing for attention.
IK: target pose -> solved joint state -> achieved pose/error. Keep target and achieved frames visually distinct. Do not claim MoveIt2 unless its actual output is used.
