import random
import math
import numpy as np
import pygame
from pygame.color import THECOLORS

import pymunk
from pymunk.vec2d import Vec2d
from pymunk.pygame_util import DrawOptions as draw
import keyboard

LENGTH_COEFF = 6
f=0.1
y_outer=4480*f
x_outer=8080*f
f2 = 0.1 # factor to multiply by all dimensions given in rules manual
x1 = (x_outer-8080*f2)/2# bottom left
y1 = (y_outer-4480*f2)/2
x2 = x1+8080*f2 #bottom right
y2 = y1
x3 = x1 #top left
y3 = y1+4480*f2
x4 = x2 #top right
y4 = y3

goal=False
prev_dist=0.0
# PyGame init
width = 808
height = 448
pygame.init()
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()

carr1 = pygame.image.load('carr1.png').convert_alpha()
carr1=pygame.transform.scale(carr1, (150, 150))
carr2 = pygame.image.load('carr2.png').convert_alpha()
carr2=pygame.transform.scale(carr2, (150, 150))
carb1 = pygame.image.load('carb1.png').convert_alpha()
carb1=pygame.transform.scale(carb1, (150, 150))
carb2 = pygame.image.load('carb2.png').convert_alpha()
carb2=pygame.transform.scale(carb2, (150, 150))
red = pygame.image.load('Red.png').convert_alpha()
red=pygame.transform.rotate(red, 90)
blue = pygame.image.load('Blue.png').convert_alpha()
blue=pygame.transform.rotate(blue, -90)
buff = pygame.image.load('buff.png').convert_alpha()
# Turn off alpha since we don't use it.
screen.set_alpha(None)

# Showing sensors and redrawing slows things down.
show_sensors = True
draw_screen = False

def check(x0, y0):
    if x0<=-50 or x0>=704 or y0<=-40 or y0>=334 :
        return  0
    if x0<=52 and y0<=82 and y0>=-13 : #top left
        return 0
    if x0>=607 and y0<=318 and y0>=222 : #bottom right
        return 0
    if x0>=530 and x0<=608 and y0<=62 : #top right
        return 0
    if x0>=48 and x0<=125 and y0>=234 : #bottom left
        return 0
    if x0>=251 and x0<=405 :
        if y0>=222 and y0<=318 : 
            return 0
        if y0>=-20 and y0<=76 : 
            return 0
    if y0>=102 and y0<=196 :
        if x0>=46 and x0<=183 :
            return 0
        if x0>=474 and x0<=610 :
            return 0
    if y0>=102 and y0<=191 and x0>=290 and x0<=366 :
        return 0
    else :
        return 1
    
def check_shoot(x0, y0):
    # if x0<=-50 or x0>=704 or y0<=-40 or y0>=334 :
    #     return  0
    if x0<=100 and y0<=121 and y0>=96 : #top left
        return 0
    if x0>=707 and y0<=354 and y0>=336 : #bottom right
        return 0
    if x0>=634 and x0<=657 and y0<=100 : #top right
        return 0
    if x0>=153 and x0<=172 and y0>=350 : #bottom left
        return 0
    if x0>=352 and x0<=454 :
        if y0>=334 and y0<=357 : 
            return 0
        if y0>=92 and y0<=115 : 
            return 0
    if y0>=215 and y0<=235 :
        if x0>=149 and x0<=233 :
            return 0
        if x0>=577 and x0<=659 :
            return 0
    if y0>=213 and y0<=240 and x0>=390 and x0<=417 :
        return 0
    else :
        return 1

def ifshoot(xr, yr, xb, yb):
    arr = range(101)
    y = 0
    m = (yr-yb)/(xr-xb+0.0001)
    for xi in arr:
        x = 2*xi + xb
        y = yb + m*(x-xb)
        print("hello", x, y, yr)
        if check_shoot(x,y)==0 :
            print("not good")
            return 0
        if y>=yr :
            print("halloween")
            return 1

class GameState:
    def __init__(self):
        # Global-ish.
        self.xr1 = 682
        self.yr1 =  323
        self.xr2 = 682
        self.yr2 =  -27
        self.xb1 = -27
        self.yb1 =  -27
        self.xb2 = -27
        self.yb2 =  323
        self.crashed = False
        self.drawoptions = draw(screen)
        # Physics stuff.
        self.space = pymunk.Space()
        self.space.gravity = pymunk.Vec2d(0., 0.)
        #self.space.add_collision_handler(1, 1, post_solve=self.car_crashed)
        #pymunk.CollisionHandler(_handler=self.new_handle,post_solve=self.car_crashed,space = self.space)
        # Create the robots.
        self.create_car(50, 50, 0,1)
        self.create_car(50, 410, 0,2)
        self.create_car(710, 410, 0,3)
        self.create_car(710, 50, 0,4)
        # Record steps.
        self.time = 0
        self.num_steps = 0
        self.goal = (400, 51)
        #self.create_obstacle(self.goal[0],self.goal[1],30)
        # screen.blit(car, ())
        screen.blit(blue, (0, 0))
        screen.blit(blue, (0, 410))
        x, y = self.robot1_body.position
        print(x, y)
        self.init_heuristic = Vec2d(self.goal[0]-x, self.goal[1]-y).get_length()
        self.prev_goal_distance = self.init_heuristic
        self.robot1_body_prev_angle = 0
        # Create walls.
        static = [
            pymunk.Segment(
                self.space.static_body,
                (0, 1), (0, height), 1),
            pymunk.Segment(
                self.space.static_body,
                (1, height), (width, height), 1),
            pymunk.Segment(
                self.space.static_body,
                (width-1, height), (width-1, 1), 1),
            pymunk.Segment(
                self.space.static_body,
                (1, 1), (width, 1), 1)
        ]
        for s in static:
            s.friction = 1.
            s.group = 1
            s.collision_type = 1
            s.color = THECOLORS['green']
        self.space.add(static)

        # Create some obstacles, semi-randomly.
        # We'll create three and they'll move around to prevent over-fitting.
        self.obstacles = []

        global prev_dist
        
        prev_dist = math.sqrt((self.goal[0]-100)*(self.goal[0]-100)+(510-self.goal[1]-100)*(510-self.goal[1]-100))
        
        self.obstacles.append(self.create_rect_obstacle(50,338,100,20))
        self.obstacles.append(self.create_rect_obstacle(404,103.5,100,20))
        self.obstacles.append(self.create_rect_obstacle(404,344.5,100,20))
        self.obstacles.append(self.create_rect_obstacle(758,103.5,100,20))
        
        self.obstacles.append(self.create_rect_obstacle(618,224,80,20))
        self.obstacles.append(self.create_rect_obstacle(190,224,80,20))
        
        self.obstacles.append(self.create_rect_obstacle(150+12.5,50,20,100))
        self.obstacles.append(self.create_rect_obstacle(808-(150+12.5),448-50,20,100))
        
        self.obstacles.append(self.center_obstacle())
        
        #self.create_buff_debuff((0, 255, 0), 400, 51, 54, 48)# buff zone
        # self.create_buff_debuff("green", 400, 51, 54, 48)# buff zone
        #self.obstacles.append(self.create_debuff( 190, 165, 54, 48))#debuff zone
        #self.create_buff_debuff( (255, 255, 0), 50, 336, 54, 48)#supply zone
        #self.create_buff_debuff((255, 255, 0), 400, 448-51, 54, 48)#supply zone
        #self.obstacles.append(self.create_debuff( 808-190, 448-165, 54, 48))#debuff
        #self.create_buff_debuff((0, 0, 255), 808-50, 448-336, 54, 48)#enemy buff

    def new_handle(self):
        pass
    
    def create_buff_debuff(self, color, x, y, w, h):
        pygame.draw.rect(screen, color, (x-(w/2), 448-(y+h/2), w, h))
        
    def create_debuff(self, x, y, w, h):
        brick_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        brick_body.position = x, y
        brick_shape = pymunk.Poly.create_box(brick_body, (w,h))
        brick_shape.elasticity = 1.0
        brick_shape.color = THECOLORS['red']
        # brick_body.color = THECOLORS['black']
        brick_shape.collision_type = 1
        
        self.space.add(brick_body, brick_shape)
        # brick_shape.position = x, 510-y
        return brick_shape
    def center_obstacle(self):
        brick_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        brick_body.position = width/2, height/2
        points= [(0, 21.21), (-21.21, 0), (0, -21.21), (21.21, 0)]
        brick_shape = pymunk.Poly(brick_body, points)
        brick_shape.elasticity = 1.0
        # brick_shape.position = width/2, height/2
        brick_shape.color = THECOLORS['black']
        brick_shape.collision_type = 1
        self.space.add(brick_body, brick_shape)
        return brick_shape
    
    def create_obstacle(self, x, y, r):
        c_body = pymunk.Body(100,100)
        c_shape = pymunk.Circle(c_body, r)
        c_shape.elasticity = 1.0
        c_shape.collision_type = 1
        c_body.position = x, y
        c_shape.color = THECOLORS["black"]
        self.space.add(c_body, c_shape)
        return c_body

    def create_rect_obstacle(self, x, y, w, h):
        brick_body = pymunk.Body(body_type=pymunk.Body.STATIC)
        brick_body.position = x, y
        brick_shape = pymunk.Poly.create_box(brick_body, (w,h))
        brick_shape.elasticity = 1.0
        brick_shape.color = THECOLORS['black']
        # brick_body.color = THECOLORS['black']
        brick_shape.collision_type = 1
        
        self.space.add(brick_body, brick_shape)
        # brick_shape.position = x, 510-y
        return brick_shape

    def create_car(self, x, y, r,nos):
        '''inertia = pymunk.moment_for_circle(1, 0, 14, (0, 0))
        self.car_body = pymunk.Body(1, inertia)
        self.car_body.position = x, y
        self.car_shape = pymunk.Circle(self.car_body, 14)
        # self.car_shape.color = THECOLORS["gray"]
        self.car_shape.elasticity = 1.0
        self.car_body.angle = r
        # screen.blit(car, (x, 510-y))
        #self.car_body_prev_angle = self.car_body.angle
        driving_direction = Vec2d(1, 0).rotated(self.car_body.angle)
        self.car_body.apply_impulse_at_local_point(driving_direction)
        self.space.add(self.car_body, self.car_shape)'''
        inertia = pymunk.moment_for_circle(1, 0, 14, (0, 0))
        if(nos==1):
            self.robot1_body = pymunk.Body(1, inertia)
            self.robot1_body.position = x, y
            self.robot1_shape = pymunk.Circle(self.robot1_body, 1)
            # self.car_shape.color = THECOLORS["gray"]
            self.robot1_shape.elasticity = 1.0
            self.robot1_body.angle = r
            # screen.blit(car, (x, 510-y))
            #self.car_body_prev_angle = self.car_body.angle
            driving_direction = Vec2d(1, 0).rotated(self.robot1_body.angle)
            self.robot1_body.apply_impulse_at_local_point(driving_direction)
            self.space.add(self.robot1_body,self.robot1_shape)
        elif(nos==2):
            self.robot2_body = pymunk.Body(1, inertia)
            self.robot2_body.position = x, y
            self.robot2_shape = pymunk.Circle(self.robot2_body, 1)
            # self.car_shape.color = THECOLORS["gray"]
            self.robot2_shape.elasticity = 1.0
            self.robot2_body.angle = r
            # screen.blit(car, (x, 510-y))
            #self.car_body_prev_angle = self.car_body.angle
            driving_direction = Vec2d(1, 0).rotated(self.robot2_body.angle)
            self.robot2_body.apply_impulse_at_local_point(driving_direction)
            self.space.add(self.robot2_body,self.robot2_shape)
        elif(nos==3):
            self.robot3_body = pymunk.Body(1, inertia)
            self.robot3_body.position = x, y
            self.robot3_shape = pymunk.Circle(self.robot3_body, 1)
            # self.car_shape.color = THECOLORS["gray"]
            self.robot3_shape.elasticity = 1.0
            self.robot3_body.angle = r
            # screen.blit(car, (x, 510-y))
            #self.car_body_prev_angle = self.car_body.angle
            driving_direction = Vec2d(1, 0).rotated(self.robot3_body.angle)
            self.robot3_body.apply_impulse_at_local_point(driving_direction)
            self.space.add(self.robot3_body,self.robot3_shape)
        else:
            self.robot4_body = pymunk.Body(1, inertia)
            self.robot4_body.position = x, y
            self.robot4_shape = pymunk.Circle(self.robot4_body, 1)
            # self.car_shape.color = THECOLORS["gray"]
            self.robot4_shape.elasticity = 1.0
            self.robot4_body.angle = r
            # screen.blit(car, (x, 510-y))
            #self.car_body_prev_angle = self.car_body.angle
            driving_direction = Vec2d(1, 0).rotated(self.robot4_body.angle)
            self.robot4_body.apply_impulse_at_local_point(driving_direction)
            self.space.add(self.robot4_body,self.robot4_shape)

    def frame_step(self,Debug,robo1,robo2,robo3,robo4,word1=None,word2=None,word3=None,word4=None):
        action = -1
        flag=1
        if keyboard.is_pressed('q'):
            flag=0
        inx1 = 0
        iny1 = 0
        inx2 = 0
        iny2 = 0
        inx3 = 0
        iny3 = 0
        inx4 = 0
        iny4 = 0
        if Debug:
            if keyboard.is_pressed('i'):
                iny4 = -0.2
            if keyboard.is_pressed('j'):
                inx4 = -0.2
            if keyboard.is_pressed('l'):
                inx4 = 0.2
            if keyboard.is_pressed('k'):
                iny4 = 0.2
            if keyboard.is_pressed('8'):
                iny3 = -0.2
            if keyboard.is_pressed('4'):
                inx3 = -0.2
            if keyboard.is_pressed('6'):
                inx3 = 0.2
            if keyboard.is_pressed('5'):
                iny3 = 0.2
            if keyboard.is_pressed('up'):
                iny2 = -0.2
            if keyboard.is_pressed('left'):
                inx2 = -0.2
            if keyboard.is_pressed('right'):
                inx2 = 0.2
            if keyboard.is_pressed('down'):
                iny2 = 0.2
            if keyboard.is_pressed('w'):
                iny1 = -0.2
            if keyboard.is_pressed('a'):
                inx1 = -0.2
            if keyboard.is_pressed('d'):
                inx1 = 0.2
            if keyboard.is_pressed('s'):
                iny1 = 0.2
            if check(self.xb1+inx1, self.yb1+iny1):
                self.xb1 += inx1
                self.yb1 += iny1
            if check(self.xb2+inx2,self.yb2+iny2):
                self.xb2 += inx2
                self.yb2 += iny2
            if check(self.xr1+inx3, self.yr1+iny3):
                self.xr1 += inx3
                self.yr1 += iny3
            if check(self.xr2+inx4,self.yr2+iny4):
                self.xr2 += inx4
                self.yr2 += iny4
            robo1.write(str(self.xb1)+" "+str(self.yb1)+"\n")
            robo2.write(str(self.xb2)+" "+str(self.yb2)+"\n")
            robo3.write(str(self.xr1)+" "+str(self.yr1)+"\n")
            robo4.write(str(self.xr2)+" "+str(self.yr2)+"\n")
            
        else :
            self.xb1,self.yb1 = float(word1[0]),float(word1[1])
            self.xb2,self.yb2 = float(word2[0]),float(word2[1])
            self.xr1,self.yr1 = float(word3[0]),float(word3[1])
            self.xr2,self.yr2 = float(word4[0]),float(word4[1])

        global prev_dist, goal, car
        # print(action)
        # reward = 0
        # if action == 0:  # Turn left.
        #     self.car_body.angle -= 0.1
        # elif action == 1:  # Turn right.
        #     self.car_body.angle += 0.1
        # elif action == 2:  # Go straight
        #     self.car_body.angle += 0
        # self.car_body.angle = self.car_body.angle%(2*math.pi)
        # # Move obstacles.
        # #if self.num_steps % 100 == 0:
        # #    self.move_obstacles()
        # #print(self.car_body.angle)
        # #print(self.car_body.angle)
        # driving_direction = Vec2d(1, 0).rotated(self.car_body.angle)
        # # print()
        # if not goal:
        #     self.car_body.velocity = 1* driving_direction
        # else:
        #     self.car_body.velocity = 0*driving_direction
        # # Update the screen and stuff.	
        screen.fill(THECOLORS["gray"])
        #self.create_buff_debuff((0, 255, 0), 404, 44.5, 54, 48)# buff zone
        # self.create_buff_debuff("green", 400, 51, 54, 48)# buff zone
        # self.create_debuff( 190, 193.5, 54, 48)#debuff zone
        #self.create_buff_debuff((255, 255, 0), 47, 279, 54, 48)#supply zone
        #self.create_buff_debuff((0, 0, 255), 404, 448-44.5, 54, 48)#supply zone
        # self.create_debuff( 810-190, 510-193.5, 54, 48)#debuff
        #self.create_buff_debuff((0, 0, 255), 808-47, 448-279, 54, 48)#enemy buff
        screen.blit(blue, (0, 0))
        screen.blit(blue, (0, 348))
        screen.blit(red, (708, 0))
        screen.blit(red, (708, 348))
        
        #draw(screen, self.space)
        # pygame.display.update()
        self.space.debug_draw(self.drawoptions)
        self.space.step(1./10)
        # x, y = self.car_body.position
        if check(self.xb1+inx1, self.yb1+iny1):
            self.xb1 += inx1
            self.yb1 += iny1
        d_b1_r1 = np.sqrt(np.square(self.xr1-self.xb1)+np.square(self.yr1-self.yb1))
        d_b1_r2 = np.sqrt(np.square(self.xr2-self.xb1)+np.square(self.yr2-self.yb1))
        d_b2_r1 = np.sqrt(np.square(self.xr1-self.xb2)+np.square(self.yr1-self.yb2))
        d_b2_r2 = np.sqrt(np.square(self.xr2-self.xb2)+np.square(self.yr2-self.yb2))

        # pygame.draw.line(screen, (255,100,0), (self.xb1,self.yb1), (0,0), 5)

        if d_b1_r1 <= 200 :
            if ifshoot(self.xr1+75, self.yr1+75, self.xb1+75, self.yb1+75):
                # print("shit")
                pygame.draw.line(screen, (255,0,255), (self.xb1+75,self.yb1+75), (self.xr1+75,self.yr1+75), 5)

        print(self.xb1,self.yb1)
        screen.blit(carr1, (self.xr1, self.yr1))
        screen.blit(carr2, (self.xr2, self.yr2))
        screen.blit(carb1, (self.xb1, self.yb1))
        screen.blit(carb2, (self.xb2, self.yb2))
        screen.blit(buff, (50-27,148))
        screen.blit(buff, (400-24,510-130))
        screen.blit(buff, (190-27,193.5+65))
        screen.blit(buff,(810-219, 510-370))
        screen.blit(buff,(400-25, 27-7))
        screen.blit(buff,(733,312-57))
        pygame.display.update()
        # # if draw_screen:
        # #     pygame.display.flip()
        # #clock.tick()
        return flag


    def move_obstacles(self):
        # Randomly move obstacles around.
        for obstacle in self.obstacles:
            #print("hello")
            speed = random.randint(1, 2)
            direction = Vec2d(1, 0).rotated(self.robot1_body.angle + random.randint(-2, 2))
            obstacle.velocity = speed * direction

    def move_cat(self):
        speed = random.randint(20, 30)
        self.robot1_body.angle -= random.randint(-1, 1)
        direction = Vec2d(1, 0).rotated(self.robot1_body.angle)
        self.robot1_body.velocity = speed * direction

    def car_is_crashed(self, readings):
        if readings[0] == 1 or readings[1] == 1 or readings[2] == 1:
            return True
        else:
            return False

    def recover_from_crash(self, driving_direction):
        """
        We hit something, so recover.
        """
        while self.crashed:
            # Go backwards.
            self.robot1_body.velocity = -5 * driving_direction
            self.crashed = False
            for i in range(10):
                #self.car_body.angle += .05  # Turn a little.
                screen.fill(THECOLORS["grey"])  # Red is scary!
                #draw(screen, self.space)
                self.space.step(1./10)
                #if draw_screen:
                #    pygame.display.flip()
                clock.tick()

    def sum_readings(self, readings):
        """Sum the number of non-zero readings."""
        tot = 0
        for i in readings:
            tot += i
        return tot

    def get_sonar_readings(self, x, y, angle):
        readings = []
        arms = []
        # print(angle)
        """
        Instead of using a grid of boolean(ish) sensors, sonar readings
        simply return N "distance" readings, one for each sonar
        we're simulating. The distance is a count of the first non-zero
        reading starting at the object. For instance, if the fifth sensor
        in a sonar "arm" is non-zero, then that arm returns a distance of 5.
        """
        for i in range(16):
            arms.append(self.make_sonar_arm(x,y))
            readings.append(self.get_arm_distance(arms[i],x,y,angle,(math.pi/8)*i, i))
        # Make our arms.
        
        
        #arm_left = self.make_sonar_arm(x, y)
        #arm_middle = arm_left
        #arm_right = arm_left

        # Rotate them and get readings.
        #readings.append(self.get_arm_distance(arm_left, x, y, angle, 0.75))
        #readings.append(self.get_arm_distance(arm_middle, x, y, angle, 0))
        #readings.append(self.get_arm_distance(arm_right, x, y, angle, -0.75))

        if show_sensors:
            pygame.display.update()

        return readings

    def get_arm_distance(self, arm, x, y, angle, offset, p):
        # Used to count the distance.
        i = 0

        # Look at each point and see if we've hit something.
        for point in arm:
            i += 1

            # Move the point to the right spot.
            rotated_p = self.get_rotated_point(
                x, y, point[0], point[1], angle + offset
            )

            # Check if we've hit something. Return the current i (distance)
            # if we did.
            if rotated_p[0] <= 0 or rotated_p[1] <= 0 or rotated_p[0] >= width or rotated_p[1] >= height:
                return i  # Sensor is off the screen.
            else:
                obs = screen.get_at((int(rotated_p[0]), int(510-rotated_p[1])))
                if self.get_track_or_not(obs) != 1:
                    return i

            if show_sensors:
                if(p==0):
                    pygame.draw.circle(screen, (255, 0, 0), (rotated_p[0], 510-rotated_p[1]), 2)
                else:
                    pygame.draw.circle(screen, (255, 255, 255), (rotated_p[0], 510-rotated_p[1]), 2)

        # Return the distance for the arm.
        return i

    def make_sonar_arm(self, x, y):
        spread = 10  # Default spread.
        distance = 20  # Gap before first sensor.
        arm_points = []
        # Make an arm. We build it flat because we'll rotate it about the
        # center later.
        for i in range(1, 40):
            arm_points.append((distance + x + (spread * i), y))

        return arm_points

    def get_rotated_point(self, x_1, y_1, x_2, y_2, radians):
        # Rotate x_2, y_2 around x_1, y_1 by angle.
        x_change = (x_2 - x_1) * math.cos(radians) + \
            (y_2 - y_1) * math.sin(radians)
        y_change = (y_1 - y_2) * math.cos(radians) - \
            (x_1 - x_2) * math.sin(radians)
        new_x = x_change + x_1
        new_y = height - (y_change + y_1)
        return int(new_x), int(new_y)

    def get_track_or_not(self, reading):
        if reading == (0, 0, 0, 255):
            return 0
        else:
            return 1
    def car_crashed(self, space, arbiter):
        if arbiter.is_first_contact:
            for contact in arbiter.contacts:
                self.crashed = True

    def car_at_buff(self, color):
        if color == (0, 255, 0, 255):
            return 1
        else:
            return 0
        
    def car_at_debuff(self, color):
        if color == (255, 0, 0, 255):
            return 1
        return 0
    
    def reset_goal(self, x, y):
        # self.goal = (int(random.random()*29031)%8100*f2, int(random.random()*10093)%5100*f2)
        # while not (self.goal[0] > x1+90 or self.goal[0] < x4-90 or self.goal[1] > y1+90 or self.goal[1] < y3-90 or screen.get_at((int(self.goal[0]), int(510-self.goal[1]))) != (0, 0, 0, 255)):
        #     self.goal = (int(random.random()*29031)%8100*f2, int(random.random()*10093)%5100*f2)
        x=100
        y=100
        return(x, y)
        
if __name__ == "__main__":
    game_state = GameState()
    flag = 1
    # game_state.frame_step(2)
    Debug = False
    if Debug:
        robo1 = open("robo1.txt","w+")
        robo2 = open("robo2.txt","w+")
        robo3 = open("robo3.txt","w+")
        robo4 = open("robo4.txt","w+")
        while flag:
            flag = game_state.frame_step(Debug,robo1,robo2,robo3,robo4)
    else:
        robo1 = open("robo1.txt","r")
        robo2 = open("robo2.txt","r")
        for line1,line2,line3,line4 in zip(robo1,robo2,robo3,robo4):
            word1 = line1.split(' ')
            word2 = line2.split(' ')
            word3 = line3.split(' ')
            word4 = line4.split(' ')
            flag = game_state.frame_step(Debug,robo1,robo2,robo3,robo4,word1,word2,word3,word4)
    
    robo1.close()
    robo2.close()
    robo3.close()
    robo4.close()