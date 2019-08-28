#!/usr/bin/env python
import sys
import copy
import rospy
import moveit_commander
import moveit_msgs.msg
import geometry_msgs.msg
from math import pi
from std_msgs.msg import String
from moveit_commander.conversions import pose_to_list
import time
import random
import numpy
from actionlib_msgs.msg import GoalStatusArray
from moveit_msgs.msg import DisplayTrajectory

class MoveGroupCom(object):
    def __init__(self):
        moveit_commander.roscpp_initialize(sys.argv)
        rospy.init_node('move_group_python_interface_tutorial', anonymous=True)

        robot = moveit_commander.RobotCommander()
        scene = moveit_commander.PlanningSceneInterface()
        group_name = "right_arm"
        self.move_group = moveit_commander.MoveGroupCommander(group_name)

        self.display_trajectory_publisher = rospy.Publisher('/move_group/display_planned_path',
                                                    moveit_msgs.msg.DisplayTrajectory,
                                                    queue_size=20)

        self.status_subsriber = rospy.Subscriber("/move_group/status", GoalStatusArray, self.goalStatus_callback)
        self.status = 1
        self.goalId = 0
        self.lastGoalId = -1
        self.reachGoal = False

        self.trajectory_subscriber = rospy.Subscriber("/move_group/display_planned_path",DisplayTrajectory,self.trajectory_callback)
        self.start = [0,0,0,0,0,0,0]
        self.traectories = None
        self.end = [0,0,0,0,0,0,0]

        # We can get the name of the reference frame for this robot:
        planning_frame = self.move_group.get_planning_frame()
        print "============ Planning frame: %s" % planning_frame

        # We can also print the name of the end-effector link for this group:
        eef_link = self.move_group.get_end_effector_link()
        print "============ End effector link: %s" % eef_link

        # We can get a list of all the groups in the robot:
        group_names = robot.get_group_names()
        print "============ Available Planning Groups:", robot.get_group_names()

        # Sometimes for debugging it is useful to print the entire state of the
        # robot:
        print "============ Printing robot state"
        print robot.get_current_state()
        print ""

    def reach_jointGoal(self,my_goal):
        # We can get the joint values from the group and adjust some of the values:
        self.reachGoal = False
        joint_goal = self.move_group.get_current_joint_values()
        self.setStart(joint_goal)
        joint_goal[0] = my_goal[0] #0
        joint_goal[1] = my_goal[1] #-pi/4
        joint_goal[2] = my_goal[2] #0
        joint_goal[3] = my_goal[3] #-pi/2
        joint_goal[4] = my_goal[4]#0
        joint_goal[5] = my_goal[5]#pi/3
        joint_goal[6] = my_goal[6]#0
        self.setEnd(joint_goal)

        # The go command can be called with joint values, poses, or without any
        # parameters if you have already set the pose or joint target for the group
        self.move_group.go(joint_goal, wait=True)

        # Calling ``stop()`` ensures that there is no residual movement
        self.move_group.stop()

        #qinjielin: clear targets after palnning with joint
        # self.move_group.clear_joint_value_targets()
    
    def setStart(self,joint_goal):
        for i in range(7):
            self.start[i] = joint_goal[i]
    
    def setEnd(self,joint_goal):
        for i in range(7):
            self.end[i] = joint_goal[i]
    
    def reach_xyzGoal(self,random_goal_value):
        pose_goal = geometry_msgs.msg.Pose()
        pose_goal.orientation.w = 1.0
        pose_goal.position.x = random_goal_value[0]#0.2
        pose_goal.position.y = random_goal_value[1]#-0.4
        pose_goal.position.z = random_goal_value[2]#0.4

        self.move_group.set_pose_target(pose_goal)

        plan = self.move_group.go(wait=True)
        # Calling `stop()` ensures that there is no residual movement
        self.move_group.stop()
        # It is always good to clear your targets after planning with poses.
        # Note: there is no equivalent function for clear_joint_value_targets()
        self.move_group.clear_pose_targets()

    def goalStatus_callback(self,msg):
        self.status = msg.status_list[0].status
        self.goalId = msg.status_list[0].goal_id.stamp.secs
        if (not (self.goalId == self.lastGoalId)):
            if(self.status == 3):
                self.lastGoalId = self.goalId
                self.reachGoal=True
                print("**************** reach new goal *****************")

    def trajectory_callback(self,msg):
        print("############### get new plan #################")
        self.traectories = []
        points = msg.trajectory[0].joint_trajectory.points
        for p in points:
            self.traectories.append(p.positions)
        
def record_trajectory(start,end,traj):

    with open('/clever/roboArm_dataset/data.txt', 'a') as f:
        f.write("start: "+str(start)+"\n")
        f.write("tajectories: "+str(traj)+"\n")
        f.write("end: "+str(end)+"\n")
    f.close()


if __name__ == "__main__":
    my_arm = MoveGroupCom()
    terminal = 0
    trajectoryNum = 5
    
    while(terminal < trajectoryNum):
        random_joint_value = numpy.random.uniform(-pi+1, pi-1, size=(7, ))
        print("random joint goal:",random_joint_value)
        my_arm.reach_jointGoal(random_joint_value)
        time.sleep(1)
        if(my_arm.reachGoal):
            terminal+=1
            start = list(my_arm.start)
            end = list(my_arm.end)
            traj = list(my_arm.traectories)
            record_trajectory(start,end,traj)

    # start = numpy.random.uniform(-pi+1, pi-1, size=(7, ))
    # end = numpy.random.uniform(-pi+1, pi-1, size=(7, ))
    # traj = numpy.random.uniform(-pi+1, pi-1, size=(3,7))
    # record_trajectory(start,end,traj)

    # random_goal_value = numpy.random.uniform(-1, 1, size=(3, ))
    # print("random_goal_value: ",random_goal_value)
    # my_arm.reach_xyzGoal(random_goal_value)