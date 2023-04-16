from ursina import *
from ursina.shaders import basic_lighting_shader
import sys
import numpy
import math

mazesize = 45 #Dont reccomend changing these values
mazehalf = (mazesize - 1)/2


class Player(Entity):
    def __init__(self, **kwargs):
        self.cursor = Entity(parent=camera.ui, model='quad', color=color.pink, scale=.008, rotation_z=45)
        super().__init__()
        self.speed = 9
        self.sprintspeed = 13
        self.height = 2
        self.camera_pivot = Entity(parent=self, y=self.height)

        camera.parent = self.camera_pivot
        camera.position = (0,0,0)
        camera.rotation = (0,0,0)
        camera.fov = 90
        mouse.locked = True
        self.mouse_sensitivity = Vec2(100, 100)

        self.gravity = 1
        self.grounded = False
        self.jump_height = 2
        self.jump_up_duration = .5
        self.fall_after = 2 # will interrupt jump up
        self.jumping = False
        self.air_time = 0
        self.staminafull = 17
        self.stamina = self.staminafull
        for key, value in kwargs.items():
            setattr(self, key ,value)

        # make sure we don't fall through the ground if we start inside it
        if self.gravity:
            ray = raycast(self.world_position+(0,self.height,0), self.down, ignore=(self,))
            if ray.hit:
                self.y = ray.world_point.y


    def update(self):
        self.rotation_y += mouse.velocity[0] * self.mouse_sensitivity[1]

        self.camera_pivot.rotation_x -= mouse.velocity[1] * self.mouse_sensitivity[0]
        self.camera_pivot.rotation_x= clamp(self.camera_pivot.rotation_x, -90, 90)

        self.direction = Vec3(
            self.forward * (held_keys['w'] - held_keys['s'])
            + self.right * (held_keys['d'] - held_keys['a'])
            ).normalized()

        if held_keys['left shift'] == 1:
            if self.stamina > 0:
                self.speed = self.sprintspeed
                self.stamina -= 1 * time.dt
            else:
                self.speed = 9
        else:
            
            self.speed = 9
            if self.stamina < self.staminafull and held_keys['left shift'] == 0:
                self.stamina += 1 * time.dt

        feet_ray = raycast(self.position+Vec3(0,0.5,0), self.direction, ignore=(self,), distance=.5, debug=False)
        head_ray = raycast(self.position+Vec3(0,self.height-.1,0), self.direction, ignore=(self,), distance=.5, debug=False)
        if not feet_ray.hit and not head_ray.hit:
            move_amount = self.direction * time.dt * self.speed

            if raycast(self.position+Vec3(-.0,1,0), Vec3(1,0,0), distance=.5, ignore=(self,)).hit:
                move_amount[0] = min(move_amount[0], 0)
            if raycast(self.position+Vec3(-.0,1,0), Vec3(-1,0,0), distance=.5, ignore=(self,)).hit:
                move_amount[0] = max(move_amount[0], 0)
            if raycast(self.position+Vec3(-.0,1,0), Vec3(0,0,1), distance=.5, ignore=(self,)).hit:
                move_amount[2] = min(move_amount[2], 0)
            if raycast(self.position+Vec3(-.0,1,0), Vec3(0,0,-1), distance=.5, ignore=(self,)).hit:
                move_amount[2] = max(move_amount[2], 0)
            self.position += move_amount

            # self.position += self.direction * self.speed * time.dt


        if self.gravity:
            # gravity
            ray = raycast(self.world_position+(0,self.height,0), self.down, ignore=(self,))
            # ray = boxcast(self.world_position+(0,2,0), self.down, ignore=(self,))

            if ray.distance <= self.height+.1:
                if not self.grounded:
                    self.land()
                self.grounded = True
                # make sure it's not a wall and that the point is not too far up
                if ray.world_normal.y > .7 and ray.world_point.y - self.world_y < .5: # walk up slope
                    self.y = ray.world_point[1]
                return
            else:
                self.grounded = False

            # if not on ground and not on way up in jump, fall
#            self.y -= min(self.air_time, ray.distance-.05) * time.dt * 100
            self.maxfallspeed = 0.05
            self.fallspeed = min(self.air_time, ray.distance - 0.05) * time.dt *self.air_time *1000
            if self.fallspeed > self.maxfallspeed:
                self.y -= self.maxfallspeed
            else:
                self.y -= self.fallspeed
            self.air_time += time.dt * .25 * self.gravity

        if self.jumping == True:
            self.jumpspeedmax = 0.1
            self.jumpspeed = ((self.jumptime - self.jump_up_duration) * time.dt * 10)
            if self.jumpspeed <= self.jumpspeedmax:
                self.y -= self.jumpspeed
            else:
                self.y -= self.jumpspeedmax
            self.jumptime += 1 * time.dt
            if self.jumptime == self.jump_up_duration or self.jumptime >= self.jump_up_duration:
                self.jumping = False
                self.gravity = True
#                invoke(self.start_fall, delay = self.fall_after)


                        
            


    def input(self, key):
        if key == 'space':
            self.jump()


    def jump(self):
        if not self.grounded:
            return

        self.grounded = False
        
        self.jumping = True
        self.jumptime = 0
        self.gravity = False

               
#        invoke(self.start_fall, delay=self.fall_after)


    def start_fall(self):
        self.jumping = False

    def land(self):
        # print('land')
        self.air_time = 0
        self.grounded = True


    def on_enable(self):
        mouse.locked = True
        self.cursor.enabled = True


    def on_disable(self):
        mouse.locked = False
        self.cursor.enabled = False

#Creating a maze------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
width = mazesize
height = width

# Create a 2D array to represent the maz
global maze
maze = [[0 for x in range(width)] for y in range(height)]

# Set the center of the maze to be open

def setcentre(h, w):
    maze[(height//2) + h][(width//2) + w] = 1
    
setcentre(0,0)
setcentre(1,0)
setcentre(1,1)
setcentre(0,1)
setcentre(1,-1)
setcentre(-1,0)
setcentre(-1,-1)
setcentre(0,-1)
setcentre(-1,1)

def generate_maze(x, y):
    directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
    random.shuffle(directions)
    for direction in directions:
        dx, dy = direction
        new_x, new_y = x + dx, y + dy
        if new_x < 0 or new_x >= width or new_y < 0 or new_y >= height:
            continue
        if maze[new_y][new_x] == 0:
            maze[new_y - dy//2][new_x - dx//2] = 1
            maze[new_y][new_x] = 1
            generate_maze(new_x, new_y)

generate_maze(width//2, height//2)


for row in maze:
    print(' '.join(['#' if cell == 0 else ' ' for cell in row]))

def translate(height, width):
    h = -(height) + mazehalf
    w = width - mazehalf
    val = maze[height][width]
    pos = [h*2, w*2]
    return pos, val


for row in maze:
    rownum = (maze.index(row))
    num = 0
    for i in row:
        pos, val = translate(rownum, num)
        num += 1
#        if val == 0:
#            e = Entity(model = 'cube', color = (0, 10, 10, 1), collider = 'box', x = pos[0], z = pos[1])

def compartmentalise():
    x_walls = []
    zpos = 22
    zind = 0
    walldetails = []
    for row in maze:
        xind = 0
        xpos = 22
        templis = []
        for i in row:
            if i == 0:
                left = xind -1
                right = xind +1
                up = zind -1
                down = zind +1
                
                if zind == 0:
                    w = 1
                else:
                    w = maze[up][xind]
                if zind == 44:
                    s = 1
                else:
                    s = maze[down][xind]
                if xind == 0:
                    a = 1
                else:
                    a = maze[zind][left]
                if xind == 44:
                    d = 1
                else:
                    d = maze[zind][right]
            

###             1 means empty for fucks sake. stupid ai
                lis = [w, a, s, d]
                try:
                    lis.remove(1)
                except ValueError:
                    pass

                try:
                    lis.remove(1)
                except ValueError:
                    pass
                
                if len(lis) == 4:
                    modeln = 'X_Intersect'
                    rot = 0
                elif len(lis) == 3:
                    modeln = 'T_Intersect'
                    if s == 0:
                        rot = 0
                    elif a == 0:
                        rot = 90
                    elif w == 0:
                        rot = 180
                    else:
                        rot = -90

                elif len(lis) == 2:
                    if w == 0 and a == 0:
                        modeln = 'L_Intersect'
                        rot = 0
                    elif w == 0 and d == 0:
                        modeln = 'L_Intersect'
                        rot = -90
                    elif d == 0 and s == 0:
                        modeln = 'L_Intersect'
                        rot = 180
                    elif a == 0 and s == 0:
                        modeln = 'L_Intersect'
                        rot = 90

                    elif w == 0 and s == 0:
                        modeln = 'I_Intersect'
                        rot = 90
                    elif a == 0 and d == 0:
                        modeln = 'I_Intersect'
                        rot = 0
                    else:
                        modeln = "H_Intersect"
                        if a == 0:
                            rot = 0
                        elif w == 0:
                            rot = 90
                        elif d == 0:
                            rot = 180
                        else:
                            rot = -90

                    


                
                elif len(lis) == 1 or len(lis) == 0:
                    print("what")

                rot += 90
                val = 30
                if modeln != None:
                    templis.append([modeln, (xpos, 0, zpos), rot])
            xpos -= 1
            xind += 1
        walldetails.append(templis)
        templis = []
        zpos -= 1
        zind += 1

    zind = 0
    zpos = 22
    outerwalldetails = []
    for row in maze:
        xind = 0
        xpos = 22
        templis = []
        if zind == 0 or zind == 44:        
            for i in row:               
                if xind != 0 and xind != 44:
                    templis.append([(xpos*val, 0, zpos*val), 0])
                    
                xind +=1
                xpos -= 1

        if zind != 0 and zind != 44:
            templis.append([(22*val, 0, zpos*val), 90])
            templis.append([(-22*val, 0, zpos*val), 90])
        zind +=1
        zpos -=1
        outerwalldetails.append(templis)

    pillardetails = [[(2*val, 0, -2*val), 180],
                     [(2*val, 0, 2*val), 90],
                     [(-2*val, 0, 2*val), 0],
                     [(-2*val, 0, -2*val), -90],
                     [(2*val, 0, -1*val), 90],
                     [(2*val, 0, 0*val), 90],
                     [(2*val, 0, 1*val), 90],
                     [(1*val, 0, -2*val), 0],
                     [(1*val, 0, 2*val), 0],
                     [(0*val, 0, 2*val), 0],
                     [(0*val, 0, -2*val), 0],
                     [(-1*val, 0, 2*val), 0],
                     [(-1*val, 0, -2*val), 0],
                     [(-2*val, 0, 1*val), 90],
                     [(-2*val, 0, -1*val), 90],
                     [(-2*val, 0, 0*val), 90]]

    return walldetails, outerwalldetails, pillardetails    


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#def solve_linear(equation,var='x'):
#    expression = equation.replace("=","-(")+")"
#    grouped = eval(expression.replace(var,'1j'))
#    return -grouped.real/grouped.imag

def PathFindMaze(maze):
    highlighted_maze = maze
    Intersections = [] #position, [0, 0, 1, 1]
    rownum = 0
    negated = []
    for row in highlighted_maze:
        columnnum = 0
        for i in row:
            if highlighted_maze[rownum][columnnum] is 0:
                w = 1
                a = 1
                s = 1
                d = 1
                lis = [1, 1, 1, 1]
                if rownum > 0:
                    w = highlighted_maze[rownum-1][columnnum]
                    if w is 0:
                        lis[0] = 0
                
                if rownum < 44:
                    s = highlighted_maze[rownum + 1][columnnum]
                    if s is 0:
                        lis[2] = 0

                if columnnum > 0:
                    a = highlighted_maze[rownum][columnnum - 1]
                    if a is 0:
                        lis[1] = 0
                        
                if columnnum < 44:
                    d = highlighted_maze[rownum][columnnum + 1]
                    if d is 0:
                        lis[3] = 0
                
                if w is 0 or a is 0 or s is 0 or d is 0:
                    while True:
                        sign = random.randint(2, 999)
                        if sign in negated:
                            pass
                        else:
                            negated.append(sign)
                            break
                    Intersections.append([sign, (columnnum, 0, rownum), lis])
                    

                        
            columnnum += 1

        rownum += 1

    axis = random.randint(0, 3)
    if axis is 0:
        chosenexit = (random.randint(1, 43), 0) #column, row
    elif axis is 1:
        chosenexit = (random.randint(1, 43), 44)
    elif axis is 2:
        chosenexit = (0, random.randint(1, 43))
    else:
        chosenexit = (44, random.randint(1, 43))
    

    if chosenexit[1] is 0: #chosenexit = [column, row]
        lis = [1, 1, 0, 1]
    elif chosenexit[1] is 44:
        lis = [0, 1, 1, 1]
    elif chosenexit[0] is 0:
        lis = [1, 1, 1, 0]
    else:
        lis = [1, 0, 1, 1]

        
    Intersections.append([1000, (chosenexit[0], 0, chosenexit[1]), lis])
    #Links Intersections

    
    for intersect in Intersections:
        sign = intersect[0]
        xpos = intersect[1][0]
        zpos = intersect[1][2]
        w = intersect[2][0]
        a = intersect[2][1]
        s = intersect[2][2]
        d = intersect[2][3]

        if w is 0:
            linear = 0
            #find next possible intersection
            for i in Intersections:
                if i[1][2] is zpos:
                    if i[1][0] < xpos:
                        if i[1][0] > linear:
                            linear = i[1][0]
                            lineardets = i

            dis = xpos - linear
            if dis > 1:
                countind = 1
                while True:
                    wx = maze[xpos - countind][zpos]
                    if wx is 0:
                        pass
                    
                    if xpos - countind == linear:
                        for intersect in Intersections:
                            if intersect[0] == Intersections[Intersections.index(lineardets)][0]:
                                intersect[0] = sign
                        Intersections[Intersections.index(lineardets)][0] = sign
                        break
                    
                    else:
                        break
                    
                    countind += 1


            else:
                for intersect in Intersections:
                    if intersect[0] == Intersections[Intersections.index(lineardets)][0]:
                        intersect[0] = sign
                Intersections[Intersections.index(lineardets)][0] = sign


        if s is 0:
            linear = 100
            #find next possible intersection
            for i in Intersections:
                if i[1][2] is zpos:
                    if i[1][0] > xpos:
                        if i[1][0] < linear:
                            linear = i[1][0]
                            lineardets = i

            dis = linear - xpos
            if dis > 1:
                countind = 1
                while True:
                    sx = maze[xpos + countind][zpos]
                    if sx is 0:
                        pass
                    
                    if xpos + countind == linear:
                        for intersect in Intersections:
                            if intersect[0] == Intersections[Intersections.index(lineardets)][0]:
                                intersect[0] = sign
                        Intersections[Intersections.index(lineardets)][0] = sign
                        break
                    
                    else:
                        break
                    
                    countind += 1


            else:
                for intersect in Intersections:
                    if intersect[0] == Intersections[Intersections.index(lineardets)][0]:
                        intersect[0] = sign
                Intersections[Intersections.index(lineardets)][0] = sign           


        if a is 0:
            linear = 100
            #find next possible intersection
            for i in Intersections:
                if i[1][0] is zpos:
                    if i[1][2] > xpos:
                        if i[1][2] < linear:
                            linear = i[1][2]
                            lineardets = i

            dis = linear - zpos
            if dis > 1:
                countind = 1
                while True:
                    ax = maze[xpos][zpos - countind]
                    if ax is 0:
                        pass
                    
                    if zpos - countind == linear:
                        for intersect in Intersections:
                            if intersect[0] == Intersections[Intersections.index(lineardets)][0]:
                                intersect[0] = sign
                        Intersections[Intersections.index(lineardets)][0] = sign
                        break
                    
                    else:
                        break
                    
                    countind += 1


            else:
                for intersect in Intersections:
                    if intersect[0] == Intersections[Intersections.index(lineardets)][0]:
                        intersect[0] = sign
                Intersections[Intersections.index(lineardets)][0] = sign

        if d is 0:
            linear = 0
            #find next possible intersection
            for i in Intersections:
                if i[1][0] is zpos:
                    if i[1][2] < xpos:
                        if i[1][2] > linear:
                            linear = i[1][2]
                            lineardets = i
            dis = zpos - linear
            if dis > 1:
                countind = 1
                while True:
                    dx = maze[xpos][zpos + countind]
                    if dx is 0:
                        pass
                    
                    if zpos + countind == linear:
                        for intersect in Intersections:
                            if intersect[0] == Intersections[Intersections.index(lineardets)][0]:
                                intersect[0] = sign
                        Intersections[Intersections.index(lineardets)][0] = sign
                        break
                    
                    else:
                        break
                    
                    countind += 1


            else:
                for intersect in Intersections:
                    if intersect[0] == Intersections[Intersections.index(lineardets)][0]:
                        intersect[0] = sign
                Intersections[Intersections.index(lineardets)][0] = sign

    for i in Intersections:
        if i[1][0] is 22 and i[1][2] is 22:
            if i[0] is 1000:
                chosenexit = chosenexit
                break
            else:
                pass

 
    return chosenexit


if __name__ == '__main__':
    window.vsync = False
    app = Ursina()
    Sky(color=color.gray)
    plane = Entity(model = 'plane',
                   collider = 'box',
                   texture = 'imagetex',
                   scale = (7.7, 1, 7.7),
                   y = -0.1)

    innerwalls = Entity()
    outerwalls = Entity()
    pillars = Entity()
    walldetails, outerwalldetails, pillardetails = compartmentalise()

#------------------MAZEGEN----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    #height constant
    val = 2
    #Centre
    countind = 0
    centrepillars = []
    for i in pillardetails:
        if countind < 4:
            centrepillars.append(Entity(model = 'L_Pillar_Inner', position = pillardetails[countind][0], rotation_y = pillardetails[countind][1], scale = (1, 0.8*val, 1), parent = pillars, y = 0.8*val/2))
        else:
            centrepillars.append(Entity(model = 'I_Pillar_Inner', position = pillardetails[countind][0], rotation_y = pillardetails[countind][1], scale = (1, 0.75*val, 1), parent = pillars, y = 0.75*val/2))

        countind += 1
    
    #Corners
    countind = 0
    cornerwalls = [[(22*30, 0, -22*30), 180],[(-22*30, 0, -22*30), -90],[(22*30, 0, 22*30), 90],[(-22*30, 0, 22*30), 0]]
    for i in cornerwalls:
        cornerwalls[countind] = Entity(model = 'L_Pillar', position = i[0], rotation_y = i[1], scale = (1, 0.85*val, 1), parent = outerwalls, y = 0.85*val/2)
        countind += 1

    #Outerwalls
    outerpillars = []
    for i in outerwalldetails:
        for j in i:
            outerpillars.append(Entity(model = 'I_Pillar', position = j[0], rotation_y = j[1], scale = (1, 0.8*val, 1), parent = outerwalls, y = 0.8*val/2))


    #Innerwalls
    innerwalls = []
    for row in walldetails:
        for i in row:
            innerwalls.append(Entity(model = i[0], position = i[1]*30, rotation_y = i[2], scale = (30, 0.7*val, 30), parent = innerwalls, y = 0.7*val/2))

    #Updating maze matrix and creating an exit  
        
    maze = [[[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []],
            [[], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], [], []]]

    # outerwalls
    countind = 0
    for i in maze[0]:
        maze[0][countind] = 1
        countind += 1

    countind = 0
    for i in maze[44]:
        maze[44][countind] = 1
        countind += 1
    
    countind = 1
    while True:
        maze[countind][0] = 1
        maze[countind][44] = 1
        countind += 1
        if countind is 45:
            break

    #innerwalls
    countind = 0
    for i in innerwalls:
        pos = innerwalls[countind].position
        xpos = int(pos[0]/30)
        zpos = int(pos[2]/30)

        maze[zpos][xpos] = 1
        

        countind += 1

    rownum = 0
    for i in maze:
        columnnum = 0
        for j in i:
            if j != 1:
                maze[rownum][columnnum] = 0
            columnnum += 1
        rownum += 1


    
    #puts intersections and their direction into a matrix, which can then use linear movements to determine if maze is solvable

    chosenexit = PathFindMaze(maze)
    for i in outerpillars:
        if int(i.position[0]) == (chosenexit[1]-22)*30 and int(i.position[2]) == (chosenexit[0]-22)*30:
            i.model = None
            i.disable
            destroy(i)
    
    player = Player(y=1, origin_y = -0.5)

    EditorCamera()
    # player.add_script(NoclipMode())
    app.run()
